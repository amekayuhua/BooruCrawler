import pandas as pd
import os
from typing import List
from .models import ImageItem
import config

class DataManager:
    def __init__(self, file_path=config.DATA_OUTPUT_PATH) -> None:
        self.file_path = file_path
        self.existing_ids = set()
        self.artist = config.ARTIST_NAME

    def makeup_filepath(self):
        if self.artist:
            filename_base = self.artist
        else:
            filename_base = config.SEARCH_TAGS.replace(' ', '_')
            
        full_filename = f"{filename_base}.csv"
        self.file_path = os.path.join(self.file_path, full_filename)
        
    def load_existing_ids(self):
        """
        读取现有的 CSV，返回一个 ID 集合给 self.exisiting_ids，用来做“增量去重”
        """
        self.makeup_filepath()
        
        if not os.path.exists(self.file_path):
            return
        
        try:
            # 只读 Id 这一列，省内存
            df = pd.read_csv(self.file_path, usecols=['Id'])
            self.existing_ids = set(df['Id'].astype(str))
            
        except Exception:
            return
        
    def save_as_csv(self, image_items: List[ImageItem]) -> None:
        if not image_items:
            return
        
        new_items_to_save = []
        
        for item in image_items:
            # 必须转成 str 对比，因为 load_existing_ids 里存的是 str
            item_id_str = str(item.id) 
            
            if item_id_str not in self.existing_ids:
                new_items_to_save.append(item)
                # 关键：把新 ID 加入集合，防止这一批数据里自己有重复，或者为了下一次调用做准备
                self.existing_ids.add(item_id_str)
        
        # --- 2. 如果过滤完没剩下东西，直接返回 ---
        if not new_items_to_save:
            print("没有新数据需要写入")
            return

        # --- 3. 转换 & 保存 ---
        # 只转换“新”数据，节省性能
        datalist = [item.to_dict() for item in new_items_to_save]
        df = pd.DataFrame(datalist)
        
        # 检查文件是否存在（决定是否写表头）
        file_exists = os.path.exists(self.file_path)
        
        try:
            df.to_csv(
                self.file_path, 
                mode='a', 
                index=False, 
                header=not file_exists, 
                encoding='utf-8-sig'
            )
            print(f"成功归档 {len(df)} 条数据到 {self.file_path}")
            
        except Exception as e:
            print(f"保存失败: {e}")