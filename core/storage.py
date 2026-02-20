import pandas as pd
import os
from typing import List
from .models import ImageItem
from .utils import *
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# 单次搜索文件和汇总数据文件的管理器类
class DataManager:
    def __init__(self, file_path: str, artist: str, tags: str) -> None:
        self.file_path = file_path
        self.existing_ids = set()
        self.artist = artist
        self.tags = tags

        

    def _makeup_filepath(self):
        if self.artist:
            filename_base = self.artist
        else:
            filename_base = self.tags.replace(' ', '_')
            
        full_filename = f"{filename_base}.csv"
        self.file_path = os.path.join(self.file_path, full_filename)
        
    def _load_existing_ids(self, file_path=None):
        """
        读取 CSV 中的 ID 用于去重。
        :param file_path: (可选) 指定要读取的文件路径。
                          如果不填，则默认读取 _makeup_filepath 生成的路径。
        """
        # 1. 确定目标路径
        if file_path:
            target_path = file_path
            # 如果是读取新文件，建议清空当前的 set，防止混淆
            self.existing_ids = set()
        else:
            self._makeup_filepath()
            target_path = self.file_path
        
        # 2. 如果文件不存在，直接返回（existing_ids 保持为空）
        if not os.path.exists(target_path):
            return
        
        # 3. 读取 ID 列
        try:
            df = pd.read_csv(target_path, usecols=['Id'])
            # 必须转为字符串，保证比对准确
            self.existing_ids = set(df['Id'].astype(str))
        except Exception:
            # 文件损坏或为空时，忽略错误
            return
        
        
    def save_as_csv(self, image_items: List[ImageItem]) -> None:
        """保存到单独的画师/标签 CSV 文件"""
        if not image_items:
            return
        
        self._load_existing_ids()
        # 此时 self.existing_ids 应该是 _load_existing_ids() 加载的单人数据
        new_items_to_save: List[ImageItem] = []
        
        for item in image_items:
            item_id_str = str(item.id) 
            if item_id_str not in self.existing_ids:
                new_items_to_save.append(item)
                self.existing_ids.add(item_id_str)
        
        if not new_items_to_save:
            print(f"没有新数据需要写入画师/标签表 {self.file_path}")
            return

        # 写入文件
        else:
            self._write_to_csv(new_items_to_save, self.file_path)
            print(f"写入 {len(new_items_to_save)} 条数据到画师/标签表 {self.file_path}")

    def save_to_summary_csv(self, image_items: List[ImageItem]) -> None:
        """
        [新增] 保存到 datasets/datas.csv 总表中
        """
        if not image_items:
            return

        # 1. 构造 datas.csv 的路径
        # self.file_path 此时已经是 "D:/.../miku.csv"
        # os.path.dirname 获取其父目录 "D:/.../"
        base_dir = os.path.dirname(self.file_path)
        summary_path = os.path.join(base_dir, "datas.csv")

        # 2. 复用 load_existing_ids 读取总表的 ID
        # 注意：这会重置 self.existing_ids 为总表的 ID 集合
        self._load_existing_ids(file_path=summary_path)
        
        # 3. 筛选在总表中不存在的数据
        new_items_for_summary = []
        for item in image_items:
            item_id_str = str(item.id)
            if item_id_str not in self.existing_ids:
                new_items_for_summary.append(item)
                # 实时添加到集合，防止本批次内重复
                self.existing_ids.add(item_id_str)
        
        if not new_items_for_summary:
            print(f"没有新数据需要写入汇总表 {summary_path}")
            return

        # 4. 写入总表
        print(f"写入 {len(new_items_for_summary)} 条数据到汇总表...")
        self._write_to_csv(new_items_for_summary, summary_path)

    def _write_to_csv(self, items: List[ImageItem], path: str):
        """内部工具方法：负责实际的 CSV 写入操作"""
        datalist = [item.to_dict(artist=self.artist) for item in items]
        df = pd.DataFrame(datalist)
        
        file_exists = os.path.exists(path)
        try:
            df.to_csv(
                path, 
                mode='a', 
                index=False, 
                header=not file_exists,
                encoding='utf-8-sig'
            )
        except Exception as e:
            print(f"保存失败 {path}: {e}")
            
            
    def generate_wordcloud(self):
        # 1. 找到最新的 CSV
        csv_path = self.file_path
        if not csv_path:
            print(f"未找到 {csv_path} ")
            return

        print(f"正在读取数据: {csv_path}")
        
        try:
            # 2. 读取 CSV，处理 Tags 列
            df = pd.read_csv(csv_path)
            file_name_no_ext = os.path.splitext(os.path.basename(csv_path))[-2]
            output_image_name = f"{file_name_no_ext}.png"
            
            # 图片保存路径 (和 CSV 在同一个文件夹)
            save_path = os.path.join(os.path.dirname(csv_path), output_image_name)
            
            # 确保 Tags 列是字符串，并且处理空值
            if 'Tags' not in df.columns:
                print("CSV 中没有 'Tags' 列！")
                return
                
            text_data = ""

            for tags_str in df['Tags'].dropna():
                # Booru 标签通常用空格分隔
                tags_list = tags_str.split(' ')
                
                for tag in tags_list:
                    cleaned = clean_tag(tag)
                    if cleaned and cleaned not in STOP_WORDS:
                        text_data += cleaned + " "

            if not text_data:
                print("没有提取到有效标签，请检查 CSV 内容。")
                return

            # 3. 生成词云
            print("正在绘制词云...")
            wc = WordCloud(
                width=1920,
                height=1080,
                background_color='white', # 背景色：black 或 white
                colormap='viridis',       # 配色方案：magma, inferno, plasma, viridis 等
                max_words=50,            # 最多显示多少个词
                font_path='msyh.ttc',     # (可选) 设置中文字体，防止乱码，Windows自带微软雅黑
                collocations=False        # 是否允许通过搭配两个词（二元组）
            ).generate(text_data)

            # 4. 展示和保存
            plt.figure(figsize=(16, 9))
            plt.imshow(wc, interpolation='bilinear')
            plt.axis('off') # 不显示坐标轴
            plt.tight_layout(pad=0)
            
            # 保存到本地
            wc.to_file(save_path)
            print(f"词云已保存至: {save_path}")
            
            # 弹出窗口显示
            plt.show()

        except Exception as e:
            print(f"发生错误: {e}")
            pass