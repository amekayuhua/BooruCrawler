import os
from .models import ImageItem
from typing import List
import logging

logger = logging.getLogger(__name__)

class ArtistRoster:
    def __init__(self, filepath):
        self.filepath = filepath
        self.artists = set()
        self._load()

    def _load(self):
        """加载本地画师名单"""
        if os.path.exists(self.filepath):
            with open(self.filepath, 'r', encoding='utf-8') as f:
                # 统一转为小写防止大小写匹配失败
                self.artists = {line.strip().lower() for line in f if line.strip()}
                logger.debug(f"加载本地画师名单完成，共 {len(self.artists)} 位")

    def add(self, artist_name):
        """新增画师到本地名单"""
        artist_name = artist_name.strip().lower()
        if artist_name and artist_name not in self.artists:
            self.artists.add(artist_name)
            
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            
            with open(self.filepath, 'a', encoding='utf-8') as f:
                f.write(f"{artist_name}\n")
            logger.info(f"新增画师: {artist_name}")
            logger.debug(f"已保存至: {self.filepath}")
            
        else:
            logger.debug(f"画师已存在，忽略: {artist_name}")

    def extract_artists(self, tags_str):
        """从标签中匹配已知画师"""
        if not tags_str:
            return []
        
        tags_set = set(tags_str.lower().split())
        matched = tags_set.intersection(self.artists)
        
        if matched:
            logger.debug(f"标签匹配到画师: {matched}")
        
        return list(matched)
    
    def assign_artists(self, image_items: List[ImageItem]) -> List[ImageItem]:
        """为缺失画师属性的图片分配画师"""
        if not image_items:
            return []

        matched_count = 0
        for item in image_items:
            if item.artist == "Unknown":
                matched_artists = self.extract_artists(item.tags)
                if matched_artists:
                    item.artist = ", ".join(matched_artists)
                    matched_count += 1
                    logger.debug(f"[{item.id}] 匹配到画师: {item.artist}")
                    
        if matched_count > 0:
            logger.debug(f"共匹配 {matched_count} 张图片的画师")
                    
        return image_items
    
    def clean_summary_dataset(self, csv_path: str) -> None:
        """扫描数据集，为Unknown数据重新匹配画师"""
        import pandas as pd
        
        if not os.path.exists(csv_path):
            logger.warning(f"数据集文件不存在: {csv_path}")
            return

        logger.info(f"开始清洗数据集: {csv_path}")
        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            logger.error(f"读取CSV失败: {e}")
            return

        if 'Artist' not in df.columns or 'Tags' not in df.columns:
            logger.warning("数据集缺少必要列：Artist 或 Tags")
            return

        updated_count = 0
        logger.debug(f"扫描数据集，共 {len(df)} 条记录")

        # 定位画师为Unknown且Tags不为空的行
        mask = (df['Artist'] == 'Unknown') & df['Tags'].notna()
        
        if not mask.any():
            logger.info("没有需要清洗的Unknown数据")
            return
        
        logger.debug(f"发现 {mask.sum()} 条Unknown记录待处理")
        
        # 批量提取并匹配画师
        def fast_match(tags_str):
            matched = self.extract_artists(str(tags_str))
            return ", ".join(matched) if matched else "Unknown"
            
        new_artists_series = df.loc[mask, 'Tags'].apply(fast_match)
        success_updates = new_artists_series[new_artists_series != "Unknown"]
        updated_count = len(success_updates)
        
        if updated_count > 0:
            df.loc[success_updates.index, 'Artist'] = success_updates
            logger.info(f"成功匹配 {updated_count} 条未知数据的画师")
            try:
                df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                logger.info(f"数据已保存: {csv_path}")
            except Exception as e:
                logger.error(f"保存CSV失败: {e}")
        else:
            logger.info("无新画师可匹配")