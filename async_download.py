import os
import asyncio
import aiohttp
import aiofiles
import config
from tools import async_timer, output_name
from tqdm import tqdm


# 操作函数
async def download_one(session, url, filepath, semaphore, pbar):
    async with semaphore:
        try:
            timeout = aiohttp.ClientTimeout(total=60)
            
            async with session.get(url, headers=config.HEADERS, proxy=config.PROXY, timeout=timeout) as response:
                if response.status == 200:
                    async with aiofiles.open(filepath, 'wb') as f:
                        async for chunk in response.content.iter_chunked(1024):
                            await f.write(chunk)
                    await asyncio.sleep(0.75)
                    return True
                
                else:
                    tqdm.write(f"{os.path.basename(filepath)} 失败: {response.status}")
                    await asyncio.sleep(1.5)
                    return False
                    
        except Exception as e:
            tqdm.write(f"出错: {e}")
            await asyncio.sleep(1.5)
            return False
        
        finally:
            pbar.update(1)
            
            
# 主函数
@async_timer
async def download_imgs_async(data_list):
    if not data_list:
        return

    name = output_name()
    save_dir = os.path.join(config.IMAGES_OUTPUT_PATH, name)

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    semaphore = asyncio.Semaphore(5) 

    async with aiohttp.ClientSession() as session:
        tasks = [] 

        existing_ids = set([int(name.split('.')[0]) for name in os.listdir(save_dir)])
        urless_ids = []
        del_list = []
        
        for row in data_list:
            img_id = row.get("Id")
            
            if img_id in existing_ids:
                del_list.append(row)
                
        data_list = [item for item in data_list if item not in del_list]
        dup_imgs = len(del_list)
        del_list = []
                
        for row in data_list:
            img_id = row.get("Id")
            img_url = row.get("File_URL")
            
            if not img_url:
                urless_ids.append(img_id)
                del_list.append(row)
            
        data_list = [item for item in data_list if item not in del_list]
   
        if dup_imgs:
            tqdm.write(f"检索到的图片存在 {dup_imgs} 个重复文件")
            
        if len(urless_ids):
            tqdm.write(f"检索到的图片里存在 {len(urless_ids)} 个无效地址")
            
            for id in urless_ids:
                tqdm.write(f'Id:{id}\n')
        
        if len(data_list):
            tqdm.write(f'开始下载 {len(data_list)} 张图片...')
            
            pbar = tqdm(total=len(data_list), desc="下载进度", unit="img")
            success_count = 0
            
            for row in data_list:
                img_url = row.get("File_URL")
                img_id = row.get("Id")

                ext = os.path.splitext(img_url)[-1] or ".jpg"
                filename = f"{img_id}{ext}"
                filepath = os.path.join(save_dir, filename)
                
                task = download_one(session, img_url, filepath, semaphore, pbar)
                tasks.append(task)
                
            results = await asyncio.gather(*tasks)
            success_count = results.count(True)
            tqdm.write(f"全部下载任务结束 成功{success_count}/总计{len(tasks)} 图片保存在: {save_dir}")

        else:
            tqdm.write("没有新图片需要下载。")
            
            
# 下载图片 非异步下载太慢了 暂时不用了
# @timmer
# def download_imgs(data_list):
#     if not data_list:
#         return

#     name = config.SEARCH_TAGS
#     if config.ARTIST_NAME:
#         name = config.ARTIST_NAME
    
#     safe_folder = name.replace('*', '_').replace('?', '_').replace(' ', '_')
#     save_dir = os.path.join(config.IMAGES_OUTPUT_PATH, safe_folder)
    
#     if not os.path.exists(save_dir):
#         os.makedirs(save_dir)

#     success_count = 0
    
#     for i, row in enumerate(data_list):
#         img_url = row.get("File_URL") # 获取我们在 parser_json 里存的高清链接
#         img_id = row.get("Id")
        
#         if not img_url:
#             tqdm.write(f"跳过 (无链接): ID {img_id}")
#             continue

#         ext = os.path.splitext(img_url)[-1]
#         if not ext: ext = ".jpg" 
        
#         filename = f"{img_id}{ext}"
#         filepath = os.path.join(save_dir, filename)

#         tqdm.write(f"[{i+1}/{len(data_list)}] 正在下载 ID: {img_id} \n", end="")

#         if os.path.exists(filepath):
#             tqdm.write("已存在，跳过。")
#             continue

#         try:
#             response = requests.get(img_url, headers=config.HEADERS, stream=True, timeout=20)
            
#             if response.status_code == 200:
#                 with open(filepath, 'wb') as f:
#                     for chunk in response.iter_content(chunk_size=1024):
#                         f.write(chunk)
                        
#                 success_count += 1
#                 time.sleep(0.2) 
                
#             else:
#                 tqdm.write(f"失败 (状态码 {response.status_code})")

#         except Exception as e:
#             tqdm.write(f"出错: {e}")
            
#     tqdm.write(f"{success_count}(总共{len(data_list)})个图片已保存在: {save_dir}")
