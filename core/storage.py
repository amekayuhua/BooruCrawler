import pandas as pd
import os
from typing import List
from .models import ImageItem
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import logging

logger = logging.getLogger(__name__)


class DataManager:
    def __init__(self, file_path: str, artist: str, tags: str, stop_words: set[str]) -> None:
        self.file_path = file_path
        self.existing_ids = set()
        self.artist = artist
        self.tags = tags
        self.stop_words = stop_words

    def _makeup_filepath(self):
        if self.artist:
            filename_base = self.artist
        else:
            filename_base = self.tags.replace(' ', '_')

        full_filename = f"{filename_base}.csv"
        self.file_path = os.path.join(self.file_path, full_filename)

    def _load_existing_ids(self, file_path=None):
        """读取CSV中的ID用于去重"""
        if file_path:
            target_path = file_path
            self.existing_ids = set()
        else:
            self._makeup_filepath()
            target_path = self.file_path

        if not os.path.exists(target_path):
            logger.debug(f"文件不存在，跳过去重: {target_path}")
            return

        try:
            df = pd.read_csv(target_path, usecols=['Id'])
            self.existing_ids = set(df['Id'].astype(str))
            logger.debug(f"加载 {len(self.existing_ids)} 条已有ID")
        except Exception as e:
            logger.debug(f"读取ID列出错（文件可能为空）: {e}")

    def save_as_csv(self, image_items: List[ImageItem]) -> None:
        """保存到单独的画师/标签CSV文件"""
        if not image_items:
            return

        self._load_existing_ids()
        new_items_to_save: List[ImageItem] = []

        for item in image_items:
            item_id_str = str(item.id) 
            if item_id_str not in self.existing_ids:
                new_items_to_save.append(item)
                self.existing_ids.add(item_id_str)

        logger.debug(f"过滤去重: {len(image_items)} -> {len(new_items_to_save)} 条新数据")

        if not new_items_to_save:
            logger.info(f"没有新数据需要写入: {self.file_path}")
            return

        self._write_to_csv(new_items_to_save, self.file_path)
        logger.info(f"保存 {len(new_items_to_save)} (共{len(image_items)}) 条数据到画师表")

    def save_to_summary_csv(self, image_items: List[ImageItem]) -> None:
        """保存到汇总数据表datas.csv"""
        if not image_items:
            return

        base_dir = os.path.dirname(self.file_path)
        summary_path = os.path.join(base_dir, "datas.csv")

        self._load_existing_ids(file_path=summary_path)

        new_items_for_summary = []
        for item in image_items:
            item_id_str = str(item.id)
            if item_id_str not in self.existing_ids:
                new_items_for_summary.append(item)
                self.existing_ids.add(item_id_str)

        logger.debug(f"过滤汇总表: {len(image_items)} -> {len(new_items_for_summary)} 条新数据")

        if not new_items_for_summary:
            logger.info(f"没有新数据需要写入汇总表")
            return

        self._write_to_csv(new_items_for_summary, summary_path)
        logger.info(f"保存 {len(new_items_for_summary)} (共{len(image_items)}) 条数据到汇总表")

    def _write_to_csv(self, items: List[ImageItem], path: str):
        """写入CSV文件"""
        datalist = [item.to_dict(artist=self.artist) for item in items]
        df = pd.DataFrame(datalist)

        file_exists = os.path.exists(path)
        logger.debug(f"写入CSV: {len(items)} 条记录到 {path}")
        try:
            df.to_csv(
                path, 
                mode='a', 
                index=False, 
                header=not file_exists,
                encoding='utf-8-sig'
            )
        except Exception as e:
            logger.error(f"保存CSV失败 {path}: {e}")

    def generate_wordcloud(self):
        csv_path = self.file_path
        if not csv_path:
            logger.warning(f"CSV路径未设置")
            return

        logger.debug(f"读取数据生成词云: {csv_path}")

        try:
            df = pd.read_csv(csv_path)
            logger.debug(f"读取 {len(df)} 条记录")

            file_name_no_ext = os.path.splitext(os.path.basename(csv_path))[-2]
            output_image_name = f"{file_name_no_ext}.png"
            save_path = os.path.join(os.path.dirname(csv_path), output_image_name)

            if "Tags" not in df.columns:
                logger.warning("CSV中缺少Tags列")
                return

            text_data = ""

            for tags_str in df["Tags"].dropna():
                tags_list = tags_str.split(" ")

                for tag in tags_list:
                    tag = tag.strip()
                    if ":" in tag:
                        continue

                    if tag.isdigit():
                        continue

                    cleaned = tag
                    if cleaned and cleaned not in self.stop_words:
                        text_data += cleaned + " "

            if not text_data:
                logger.warning("没有提取到有效标签")
                return

            logger.info("生成词云...")
            wc = WordCloud(
                width=1920,
                height=1080,
                background_color='white',
                colormap='viridis',
                max_words=50,
                font_path='msyh.ttc',
                collocations=False
            ).generate(text_data)

            plt.figure(figsize=(16, 9))
            plt.imshow(wc, interpolation='bilinear')
            plt.axis('off')
            plt.tight_layout(pad=0)

            wc.to_file(save_path)
            logger.info(f"词云已保存: {save_path}")
            # plt.show()

        except Exception as e:
            logger.error(f"生成词云失败: {e}")
