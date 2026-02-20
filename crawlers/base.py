from abc import ABC, abstractmethod
from core.models import ImageItem
import requests
import time
import aiohttp
import asyncio
import math
from typing import List


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
        """
        子类必须实现：
        根据本站点的搜索语法特性，将 tags 清洗为合法的文件系统名称。
        """
        pass
        
    @abstractmethod
    def _get_sort_string(self, sort_by, desc) -> str:
        """
        抽象方法：强制子类告诉我，你们家的排序语法长什么样？
        """
        pass
    
    def assemble_tags(self, base_tags, artist, rating, sort_by, desc):
        """
        通用标签组装逻辑。
        子类如果规则不一样（比如 D 站的排序），需要重写这个方法。
        """
        tags_list = []

        if artist:    tags_list.append(artist)
        if base_tags: tags_list.append(base_tags)
        if rating:    tags_list.append(f"rating:{rating}")
        
        # 留给子类去处理 unique 的部分
        specific_part = self._get_sort_string(sort_by, desc) 
        if specific_part:
            tags_list.append(specific_part)
            
        return " ".join(tags_list)

    @abstractmethod
    def _get_count(self, params) -> int:
        """子类必须实现：如何从响应中提取图片总数"""
        pass
    
    @abstractmethod
    def _build_params(self, tags, page, limit) -> dict:
        """子类必须实现：如何组装 URL 参数"""
        pass
    
    @abstractmethod
    def _parse_json_list(self, json_data) -> list:
        '''子类需实现对不同json的解析'''
        pass

    @abstractmethod
    def _normalize_data(self, raw_post) -> ImageItem:
        """子类必须实现：把网站乱七八糟的 JSON 字段清洗成标准的 ImageItem"""
        pass
    
    @abstractmethod
    def get_total_count(self, tags) -> int:
        """
        只负责发送探测包，返回搜索结果的总数量
        """
        pass
    
    
    # --- 新增：单个页面异步抓取逻辑 ---
    async def _fetch_page_async(self, session, tags, page, limit, semaphore):
        """
        协程：抓取单页数据
        """
        async with semaphore:  # 限制并发数
            params = self._build_params(tags, page, limit)
            # 处理代理 (aiohttp 使用字符串 proxy)
            req_proxy = self.proxy if isinstance(self.proxy, str) else None
            
            try:
                timeout = aiohttp.ClientTimeout(total=20) # 设置超时
                async with session.get(self.base_url, params=params, headers=self.headers, proxy=req_proxy, timeout=timeout, ssl=False) as response:
                    if response.status != 200:
                        print(f"[警告] 第 {page} 页请求失败，状态码: {response.status}")
                        return []
                    
                    json_data = await response.json()
                    raw_posts = self._parse_json_list(json_data)
                    
                    # 在这里进行清洗
                    valid_items = []
                    for raw_post in raw_posts:
                        item = self._normalize_data(raw_post)
                        if item:
                            valid_items.append(item)
                    
                    print(f"第 {page} 页获取到 {len(valid_items)} 张有效元数据")
                    await asyncio.sleep(0.5)
                    return valid_items
                
            except Exception as e:
                print(f"[错误] 第 {page} 页发生异常: {e}")
                return []

    # --- 修改：主抓取入口 ---
    async def _fetch_posts_core(self, tags: str, limit_num: int) -> List[ImageItem]:
        """
        异步批量获取元数据
        """
        target_count = limit_num
        # 计算需要多少页 (向上取整)
        # 例如需要 250 张，每页 100，则需要 ceil(2.5) = 3 页
        total_pages = math.ceil(target_count / self.MAX_LIMIT)
        
        print(f"获取 {target_count} 张。预计并发请求 {total_pages} 页...")

        # 限制并发数为 5 (防止 429 Too Many Requests)
        semaphore = asyncio.Semaphore(5)
        
        all_items = []

        async with aiohttp.ClientSession() as session:
            tasks = []
            for page in range(total_pages):
                # 创建每一页的任务
                task = asyncio.create_task(
                    self._fetch_page_async(session, tags, page, self.MAX_LIMIT, semaphore)
                )
                tasks.append(task)
            
            # 等待所有页面抓取完成
            results = await asyncio.gather(*tasks)
            
            # 展平结果列表 [[item1, item2], [item3]] -> [item1, item2, item3]
            for page_items in results:
                all_items.extend(page_items)

        # 截取需要的数量
        final_items = all_items[:target_count]
        print(f"元数据抓取完成: 实际获得 {len(final_items)} 张图片的数据")
        return final_items
    
    def start_crawling(self, tags: str, limit_num: int) -> List[ImageItem]:
        """
        [对外同步入口] 封装了 asyncio 的复杂性，供 run.py 直接调用
        """
        try:
            # 正常运行
            return asyncio.run(self._fetch_posts_core(tags, limit_num))
        except RuntimeError:
            # 兼容 Jupyter Notebook 或已有 EventLoop 的环境
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self._fetch_posts_core(tags, limit_num))