import os
import asyncio
import aiohttp
import aiofiles
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    MofNCompleteColumn,
    TimeRemainingColumn
)
from core.log_config import console
from typing import List
from core.models import ImageItem
import logging

logger = logging.getLogger(__name__)

class Downloader:
    def __init__(self, save_path, artist, tags, headers, proxy, semaphore_limit=5):
        self.save_path = save_path
        self.semaphore = asyncio.Semaphore(semaphore_limit)

        if artist:
            self.sub_folder = artist
        else:
            self.sub_folder = tags

        self.save_dir = os.path.join(self.save_path, self.sub_folder)

        self.proxy = proxy
        self.headers = headers
        self.last_request_time = 0
        self.request_interval = 0.1
        

    async def _download_one(self, session, item: ImageItem, filepath: str, progress, task_id):
        """单个图片下载协程"""
        async with self.semaphore:
            # --- 核心限速逻辑 ---
            now = asyncio.get_event_loop().time()
            wait_time = self.last_request_time + self.request_interval - now
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            self.last_request_time = asyncio.get_event_loop().time()
            # ------------------
            
            try:
                logger.debug(f"开始下载: {item.filename}")
                timeout = aiohttp.ClientTimeout(
                    connect=10,
                    sock_read=30,
                    total=None,
                )

                async with session.get(item.url, headers=self.headers, proxy=self.proxy, timeout=timeout) as response:
                    if response.status == 200:
                        async with aiofiles.open(filepath, 'wb') as f:
                            async for chunk in response.content.iter_chunked(128 * 1024):
                                await f.write(chunk)

                        logger.debug(f"下载成功: {item.filename}")
                        return True
                    else:
                        logger.warning(f"[HTTP {response.status}] {item.filename}")
                        return False
                    
            except asyncio.TimeoutError:
                logger.warning(f"[超时失败] {item.filename} : {item.source} 网络连接或读取数据超时")
                return False
            except Exception as e:
                logger.warning(f"[下载失败] {item.filename} : {item.source} {e}")
                return False

            finally:
                progress.update(task_id, advance=1)

    async def _download_batch(self, image_items: List[ImageItem], download_videos: bool):
        """异步批量下载主逻辑"""
        if not image_items:
            logger.info("没有图片需要下载")
            return

        os.makedirs(self.save_dir, exist_ok=True)
        existing_files = set(os.listdir(self.save_dir))
        
        tasks_data = []
        video_filtered_count = 0

        for item in image_items:
            if item.is_video and not download_videos:
                video_filtered_count += 1
                continue
            
            if not item.url or item.filename in existing_files:
                continue

            filepath = os.path.join(self.save_dir, item.filename)
            tasks_data.append((item, filepath))

        if video_filtered_count > 0:
            logger.debug(f"根据配置跳过了 {video_filtered_count} 个视频文件")

        if not tasks_data:
            logger.debug("所有符合条件的文件均已存在或被跳过")
            return

        total_img_task = sum(1 for item, _ in tasks_data if not item.is_video)
        total_vid_task = sum(1 for item, _ in tasks_data if item.is_video)

        logger.info(f"开始下载任务: [图片: {total_img_task} | 视频: {total_vid_task}]")

        async with aiohttp.ClientSession() as session:
            with Progress(
                TextColumn("        "),
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description:<20}"),
                BarColumn(),
                MofNCompleteColumn(),
                TaskProgressColumn(),
                TimeRemainingColumn(),
                console=console,
                transient=False  
            ) as progress:

                download_task = progress.add_task("正在下载数据中...", total=len(tasks_data))
                
                tasks = [
                    self._download_one(session, item, filepath, progress, download_task)
                    for item, filepath in tasks_data
                ]

                results = await asyncio.gather(*tasks)

        success_img = 0
        success_vid = 0

        for (item, _), is_success in zip(tasks_data, results):
            if is_success:
                if item.is_video:
                    success_vid += 1
                else:
                    success_img += 1

        if total_img_task > 0:
            logger.info(f"图片: {success_img}/{total_img_task} 成功")
        if total_vid_task > 0:
            logger.info(f"视频: {success_vid}/{total_vid_task} 成功")
        
        total_success = success_img + success_vid
        logger.info(f"总计成功: {total_success}/{len(tasks_data)}")
        logger.info(f"保存位置: {self.save_dir}")

    def download(self, image_items: List[ImageItem], download_videos: bool):
        """供 run.py 直接调用的同步入口"""
        logger.debug(f"下载器启动，共 {len(image_items)} 张图片待处理")
        try:
            asyncio.run(self._download_batch(image_items, download_videos))
        except RuntimeError:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self._download_batch(image_items, download_videos))
