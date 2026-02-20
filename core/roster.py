import os
from .models import ImageItem
from typing import List

class ArtistRoster:
    def __init__(self, filepath):
        self.filepath = filepath
        self.artists = set()
        self._load()

    def _load(self):
        """加载本地画师名单"""
        if os.path.exists(self.filepath):
            with open(self.filepath, 'r', encoding='utf-8') as f:
                # 统一转为小写，防止大小写导致匹配失败
                self.artists = {line.strip().lower() for line in f if line.strip()}

    def add(self, artist_name):
        """新增画师到本地名单"""
        artist_name = artist_name.strip().lower()
        if artist_name and artist_name not in self.artists:
            self.artists.add(artist_name)
            
            # 确保父文件夹存在
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            
            # 追加写入文件
            with open(self.filepath, 'a', encoding='utf-8') as f:
                f.write(f"{artist_name}\n")
            print(f"已将新画师 '{artist_name}' 自动收录至本地名单")
            
        else:
            print(f"{artist_name} 已在画师名册中，无需保存")

    def extract_artists(self, tags_str):
        """从一堆标签中提取出属于画师名单的词"""
        if not tags_str:
            return []
        
        # 将图片的 tags 字符串按空格拆分为集合
        tags_set = set(tags_str.lower().split())
        
        # 利用集合的交集运算，瞬间找出哪些 tag 在画师名单中
        matched = tags_set.intersection(self.artists)
        
        return list(matched)
    
    def assign_artists(self, image_items: List[ImageItem]) -> List[ImageItem]:
        """
        批量检查并为缺失画师属性的图片分配画师
        :param image_items: 爬虫返回的 ImageItem 列表
        :return: 处理后的 ImageItem 列表
        """
        if not image_items:
            return []

        for item in image_items:
            # 针对没有带 artist 属性的图片进行本地知识库匹配
            if item.artist == "Unknown":
                matched_artists = self.extract_artists(item.tags)
                if matched_artists:
                    # 允许多个画师，用逗号和空格拼接
                    item.artist = ", ".join(matched_artists)
                    
        return image_items
    
    def clean_summary_dataset(self, csv_path: str) -> None:
        """
        回溯清洗：扫描本地汇总数据集 (如 datas.csv)，
        为以前保存的 "Unknown" 数据重新匹配画师名。
        """
        import pandas as pd
        
        if not os.path.exists(csv_path):
            print(f"找不到数据集文件: {csv_path}")
            return

        print(f"正在读取并分析数据集: {csv_path} ...")
        try:
            # 读取数据
            df = pd.read_csv(csv_path)
        except Exception as e:
            print(f"读取 CSV 失败: {e}")
            return

        # 检查必要的列是否存在
        if 'Artist' not in df.columns or 'Tags' not in df.columns:
            print("数据集中缺少 'Artist' 或 'Tags' 列，无法清洗。")
            return

        updated_count = 0

       # 1. 创建掩码 (Mask)：定位画师为 'Unknown' 且 Tags 不是空值的行
        mask = (df['Artist'] == 'Unknown') & df['Tags'].notna()
        
        # 如果没有符合条件的行，直接跳过
        if not mask.any():
            print("扫描完成，没有需要清洗的 Unknown 数据。")
            return
            
        # 2. 定义批量提取函数
        def fast_match(tags_str):
            matched = self.extract_artists(str(tags_str))
            return ", ".join(matched) if matched else "Unknown"
            
        # 3. 仅对符合条件的行的 'Tags' 列应用提取操作，生成新的画师序列
        new_artists_series = df.loc[mask, 'Tags'].apply(fast_match)
        
        # 4. 筛选出真正匹配到了新画师的数据 (即返回值不再是 'Unknown' 的数据)
        success_updates = new_artists_series[new_artists_series != "Unknown"]
        updated_count = len(success_updates)
        
        # 5. 批量将新画师名称覆盖回原 DataFrame 中
        if updated_count > 0:
            df.loc[success_updates.index, 'Artist'] = success_updates

        # 如果有数据被更新了，就覆写保存原文件
        if updated_count > 0:
            print(f"成功为 {updated_count} 条历史未知数据添加画师名。")
            try:
                # index=False 保证不会多出一列行号，utf-8-sig 防止中文乱码
                df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                print(f"数据已成功覆写并保存至: {csv_path}")
            except Exception as e:
                print(f"保存修改后的 CSV 失败: {e}")
        else:
            print("扫描完成，当前名单中没有能匹配上历史未知数据的新画师。")