import os
import asyncio
import aiohttp
import aiofiles
from tqdm import tqdm
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

    async def _download_one(self, session, item: ImageItem, filepath: str, pbar: tqdm):
        """单个图片下载协程"""
        async with self.semaphore:
            try:
                logger.debug(f"开始下载: {item.filename}")
                timeout = aiohttp.ClientTimeout(total=60)
                
                async with session.get(item.url, headers=self.headers, proxy=self.proxy, timeout=timeout) as response:
                    if response.status == 200:
                        async with aiofiles.open(filepath, 'wb') as f:
                            async for chunk in response.content.iter_chunked(1024):
                                await f.write(chunk)
                        
                        logger.debug(f"下载成功: {item.filename}")
                        await asyncio.sleep(0.1)
                        return True
                    else:
                        logger.warning(f"[HTTP {response.status}] {item.filename}")
                        return False
                        
            except Exception as e:
                logger.warning(f"[下载失败] {item.filename}: {e}")
                return False
            
            finally:
                pbar.update(1)

    async def _download_batch(self, image_items: List[ImageItem]):
        """异步批量下载主逻辑"""
        if not image_items:
            logger.info("没有图片需要下载")
            return

        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
            logger.info(f"创建目录: {self.save_dir}")

        logger.debug(f"扫描本地已有文件: {self.save_dir}")
        existing_files = set(os.listdir(self.save_dir))
        logger.debug(f"发现 {len(existing_files)} 个本地文件")
        tasks_data = []

        for item in image_items:
            if not item.url:
                logger.debug(f"跳过无URL的项目: {item.filename}")
                continue
                
            if item.filename in existing_files:
                logger.debug(f"文件已存在，跳过: {item.filename}")
                continue
            
            filepath = os.path.join(self.save_dir, item.filename)
            tasks_data.append((item, filepath))

        skip_count = len(image_items) - len(tasks_data)
        if skip_count > 0:
            logger.info(f"跳过 {skip_count} 张已存在的图片")

        if not tasks_data:
            logger.info("所有图片均已下载完成")
            return

        logger.info(f"开始下载 {len(tasks_data)} 张新图片...")

        async with aiohttp.ClientSession() as session:
            pbar = tqdm(total=len(tasks_data), desc="下载进度", unit="img")
            
            tasks = [
                self._download_one(session, item, filepath, pbar)
                for item, filepath in tasks_data
            ]
            
            results = await asyncio.gather(*tasks)
            
            pbar.close()
            
            success_count = results.count(True)
            logger.info(f"下载完成: {success_count}/{len(tasks_data)} 成功")
            logger.info(f"保存位置: {self.save_dir}")

    def download(self, image_items: List[ImageItem]):
        """供 run.py 直接调用的同步入口"""
        logger.debug(f"下载器启动，共 {len(image_items)} 张图片待处理")
        try:
            asyncio.run(self._download_batch(image_items))
        except RuntimeError:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self._download_batch(image_items))