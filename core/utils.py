# import functools
# import time
# import config
import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import os
import glob


# def timmer(func):
#     def wrapper(*args):
#         t1 = time.time()
#         func(*args)
#         t2 = time.time()
#         print(f"总耗时: {t2 - t1:.2f} 秒")
#     return wrapper


# def async_timer(func):
#     """
#     专门用于测量 async 函数执行时间的装饰器
#     """
#     @functools.wraps(func)
#     async def wrapper(*args, **kwargs):
#         start_time = time.time()
#         result = await func(*args, **kwargs)
#         end_time = time.time()
#         print(f"总耗时: {end_time - start_time:.2f} 秒")
#         return result
        
#     return wrapper


# def output_name() -> str:
#     if config.ARTIST_NAME:
#         name = config.ARTIST_NAME
#         return name
    
#     else:
#         name = config.SEARCH_TAGS
#         return name
    
    
# ================= 配置区域 =================
# CSV 文件所在目录 (根据你的 config.IMAGES_OUTPUT_PATH 修改)
DATA_DIR = r"D:\pyworks\BooruCrawler\output\datasets" 

# 输出图片文件名
OUTPUT_IMAGE = "tag_cloud.png"

# 不需要显示的无意义标签 (停用词)
STOP_WORDS = {
    "absurdres", "highres", "translated", "commentary_request", 
    "check_commentary", "bilibili", "weibo"
}
# ===========================================

def get_latest_csv(directory):
    """自动获取目录下最新的 CSV 文件"""
    list_of_files = glob.glob(os.path.join(directory, '*.csv'))
    if not list_of_files:
        return None
    return max(list_of_files, key=os.path.getctime)

def clean_tag(tag):
    """
    清洗标签逻辑：
    1. 去掉 rating:xxx, score:xxx, user:xxx 等元数据
    2. 去掉包含括号的标签 (通常是作品名或角色名备注) -> 可选
    """
    tag = tag.strip()
    
    # 过滤元数据标签 (包含冒号的通常是 meta tags)
    if ':' in tag:
        return None
        
    # 过滤一些纯数字或无意义字符
    if tag.isdigit():
        return None
        
    return tag

def generate_cloud():
    # 1. 找到最新的 CSV
    csv_path = get_latest_csv(DATA_DIR)
    if not csv_path:
        print(f"在 {DATA_DIR} 下没有找到 CSV 文件！")
        return

    print(f"正在读取数据: {csv_path}")
    
    try:
        # 2. 读取 CSV，处理 Tags 列
        df = pd.read_csv(csv_path)
        file_name_no_ext = os.path.splitext(os.path.basename(csv_path))[0]
        output_image_name = f"{file_name_no_ext}.png"
        
        # 图片保存路径 (和 CSV 在同一个文件夹)
        save_path = os.path.join(os.path.dirname(csv_path), output_image_name)
        
        # 确保 Tags 列是字符串，并且处理空值
        if 'Tags' not in df.columns:
            print("CSV 中没有 'Tags' 列！")
            return
            
        text_data = ""
        print("正在分析标签频率...")

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

if __name__ == "__main__":
    generate_cloud()
