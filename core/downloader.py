import os
import asyncio
import aiohttp
import aiofiles
from tqdm import tqdm
from typing import List
from core.models import ImageItem

class Downloader:
    def __init__(self, save_path, artist, tags, headers, proxy, semaphore_limit=5):

        self.save_path = save_path
        self.semaphore = asyncio.Semaphore(semaphore_limit)
        
        # 确定子文件夹名称 (优先画师名，其次标签名)
        if artist:
            self.sub_folder = artist
        else:
            self.sub_folder = tags
            
        self.save_dir = os.path.join(self.save_path, self.sub_folder)
        
        self.proxy = proxy
        self.headers = headers

    async def _download_one(self, session, item: ImageItem, filepath: str, pbar: tqdm):
        """
        单个图片下载协程
        """
        async with self.semaphore:
            try:
                # 设置超时
                timeout = aiohttp.ClientTimeout(total=60)
                
                # 构造代理字典 (aiohttp 只需要字符串类型的 proxy)
                # 注意：requests 需要 {'http': ...}，但 aiohttp 通常直接传字符串 "http://..."
                
                async with session.get(item.url, headers=self.headers, proxy=self.proxy, timeout=timeout) as response:
                    if response.status == 200:
                        async with aiofiles.open(filepath, 'wb') as f:
                            # 分块写入文件
                            async for chunk in response.content.iter_chunked(1024):
                                await f.write(chunk)
                        
                        # 稍微歇一下，避免IO过热
                        await asyncio.sleep(0.1) 
                        return True
                    else:
                        # 下载失败不报错，只打印
                        tqdm.write(f"[失败 {response.status}] {item.filename}")
                        return False
                        
            except Exception as e:
                tqdm.write(f"[出错] {item.filename}: {e}")
                return False
            
            finally:
                pbar.update(1)

    async def _download_batch(self, image_items: List[ImageItem]):
        """
        异步批量下载的主逻辑
        """
        if not image_items:
            print("没有图片需要下载。")
            return

        # 1. 创建目录
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
            print(f"创建目录: {self.save_dir}")

        # 2. 增量去重：检查本地已有的文件
        # 获取目录下所有文件名
        existing_files = set(os.listdir(self.save_dir))
        
        tasks_data = [] # 待下载的任务列表 [(item, filepath), ...]

        for item in image_items:
            if not item.url:
                continue
                
            # 使用 ImageItem 自动生成的标准文件名 (id.ext)
            if item.filename in existing_files:
                continue
            
            filepath = os.path.join(self.save_dir, item.filename)
            tasks_data.append((item, filepath))

        # 3. 汇报跳过情况
        skip_count = len(image_items) - len(tasks_data)
        if skip_count > 0:
            print(f"跳过 {skip_count} 张已存在的图片。")

        if not tasks_data:
            print("所有图片均已下载完成！")
            return

        print(f"开始下载 {len(tasks_data)} 张新图片...")

        # 4. 启动异步 Session
        async with aiohttp.ClientSession() as session:
            # 初始化进度条
            pbar = tqdm(total=len(tasks_data), desc="下载进度", unit="img")
            
            # 创建任务列表
            tasks = [
                self._download_one(session, item, filepath, pbar)
                for item, filepath in tasks_data
            ]
            
            # 并发执行所有任务
            results = await asyncio.gather(*tasks)
            
            pbar.close()
            
            # 统计结果
            success_count = results.count(True)
            print(f"下载结束: 成功 {success_count} / 总计 {len(tasks)}")
            print(f"保存路径: {self.save_dir}")

    def download(self, image_items: List[ImageItem]):
        """
        [同步入口] 供 run.py 直接调用
        """
        # Windows 下 asyncio 的事件循环策略问题处理
        try:
            asyncio.run(self._download_batch(image_items))
        except RuntimeError:
            # 如果你在 Jupyter Notebook 里跑，或者 loop 已经运行，需要用 create_task (这里主要针对普通脚本)
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self._download_batch(image_items))