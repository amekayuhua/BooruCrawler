from abc import ABC, abstractmethod
from core.models import ImageItem
import aiohttp
import asyncio
import math
from typing import List
import logging 
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn, MofNCompleteColumn
from core.log_config import console

logger = logging.getLogger(__name__)

class BaseBoard(ABC):
    MAX_LIMIT = 100
    
    def __init__(self, api_key=None, user_id=None, proxy=None, headers=None):
        self.api_key = api_key
        self.user_id = user_id
        self.proxy = proxy
        self.headers = headers
        self.base_url = ""
    
    # 在子类中应该是一个静态方法 只获取config.SEARCH_TAGS 放在不同的子类下实现不同的清洗逻辑
    @abstractmethod
    def get_safe_tag_name(self, tags: str) -> str:
        """清洗标签为合法的文件名"""
        pass
        
    @abstractmethod
    def _get_sort_string(self, sort_by, desc) -> str:
        """子类实现：返回该站点的排序语句"""
        pass
    
    def assemble_tags(self, base_tags, artist, rating, sort_by, desc):
        """组装搜索标签（子类如需特殊规则可重写此方法）"""
        tags_list = []

        if artist:    tags_list.append(artist)
        if base_tags: tags_list.append(base_tags)
        if rating:    tags_list.append(f"rating:{rating}")
        
        specific_part = self._get_sort_string(sort_by, desc) 
        if specific_part:
            tags_list.append(specific_part)
            
        return " ".join(tags_list)

    @abstractmethod
    def _get_count(self, params) -> int:
        """子类实现：从响应中提取图片总数"""
        pass
    
    @abstractmethod
    def _build_params(self, tags, page, limit) -> dict:
        """子类实现：组装URL参数"""
        pass
    
    @abstractmethod
    def _parse_json_list(self, json_data) -> list:
        """子类实现：解析JSON数据"""
        pass

    @abstractmethod
    def _normalize_data(self, raw_post) -> ImageItem:
        """子类实现：将原始数据转换为标准ImageItem"""
        pass
    
    @abstractmethod
    def get_total_count(self, tags) -> int:
        """发送测试请求，返回搜索结果的总数量"""
        pass
    
    
    async def _fetch_page_async(self, session, tags, page, limit, semaphore, progress, task_id):
        """协程：抓取单页数据"""
        async with semaphore:
            params = self._build_params(tags, page, limit)
            page += 1
            req_proxy = self.proxy if isinstance(self.proxy, str) else None
            
            try:
                timeout = aiohttp.ClientTimeout(total=20)
                async with session.get(self.base_url, params=params, headers=self.headers, proxy=req_proxy, timeout=timeout, ssl=False) as response:
                    if response.status != 200:
                        logger.warning(f"第 {page} 页请求失败: HTTP {response.status}")
                        return []
                    
                    json_data = await response.json()
                    raw_posts = self._parse_json_list(json_data)
                    
                    valid_items = []
                    for raw_post in raw_posts:
                        item = self._normalize_data(raw_post)
                        if item:
                            valid_items.append(item)
                    
                    logger.debug(f"第{page}页获取{len(valid_items)}条有效数据")
                    await asyncio.sleep(0.5)
                    return valid_items
                
            except Exception as e:
                logger.error(f"第 {page} 页抓取失败: {e}")
                return []
            
            finally:
                # pbar.update(1)
                progress.update(task_id, advance=1)

    async def _fetch_posts_core(self, tags: str, limit_num: int) -> List[ImageItem]:
        """异步批量获取元数据"""
        target_count = limit_num
        total_pages = math.ceil(target_count / self.MAX_LIMIT)
        
        logger.info(f"准备获取 {target_count} 张图片，共 {total_pages} 页")
        logger.debug(f"页面大小: {self.MAX_LIMIT}，并发数: 5")

        semaphore = asyncio.Semaphore(5)
        all_items = []

        async with aiohttp.ClientSession() as session:
            tasks = []
            
            with Progress(
                TextColumn("        "),
                SpinnerColumn(),
                TextColumn("[cyan][progress.description]{task.description:<20}"),
                BarColumn(),
                MofNCompleteColumn(),
                TaskProgressColumn(),
                TimeRemainingColumn(),
                console=console,
                transient=False            
            ) as progress:
                
                task_id = progress.add_task("正在抓取元数据...", total=total_pages)
                
                for page in range(total_pages):
                    task = asyncio.create_task(
                        self._fetch_page_async(
                            session, tags, page, self.MAX_LIMIT, 
                            semaphore, progress, task_id
                        )
                    )
                    tasks.append(task)
            
            # with tqdm(total=total_pages, desc="获取页面元数据", unit="页") as pbar:
            #     for page in range(total_pages):
            #         task = asyncio.create_task(
            #             self._fetch_page_async(session, tags, page, self.MAX_LIMIT, semaphore, pbar)
            #         )
            #         tasks.append(task)
            
                results = await asyncio.gather(*tasks)
            
            for page_items in results:
                all_items.extend(page_items)

        final_items = all_items[:target_count]
        logger.info(f"元数据获取完成: {len(final_items)}/{target_count} 张图片/视频信息")
        return final_items
    
    def start_crawling(self, tags: str, limit_num: int) -> List[ImageItem]:
        """爬虫同步入口，供run.py直接调用"""
        logger.debug(f"启动爬虫: 标签={tags}, 数量={limit_num}")
        try:
            return asyncio.run(self._fetch_posts_core(tags, limit_num))
        except RuntimeError:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self._fetch_posts_core(tags, limit_num))