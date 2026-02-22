import os
import sys
import pandas as pd

# 将项目根目录加入系统路径，以便导入 core 模块
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from core.database import DBManager
from core.models import ImageItem

# ================= 配置区域 =================
CSV_PATH = r"D:\pyworks\BooruCrawler\output\datasets\datas.csv"
DB_PATH = r"D:\pyworks\python数据处理\sql_practices\booru_gallery.db"
# ==========================================

def import_csv_to_db():
    if not os.path.exists(CSV_PATH):
        print(f"找不到 CSV 文件: {CSV_PATH}")
        return

    print("⏳ 正在读取 CSV 数据...")
    # fillna('') 是为了防止 pandas 将空单元格解析为 float('nan') 导致类型报错
    df = pd.read_csv(CSV_PATH).fillna('')

    items_to_save = []
    
    # 1. 遍历 CSV 每一行，重新组装为 ImageItem
    for index, row in df.iterrows():
        # 解析尺寸 "1920x1080"
        size_str = str(row.get('Size', ''))
        width, height = 0, 0
        if 'x' in size_str:
            try:
                w_str, h_str = size_str.split('x', 1)
                width = int(w_str)
                height = int(h_str)
            except ValueError:
                pass # 解析失败则默认为 0
        
        # 确保整型数据不会报错
        try:
            post_id = int(row.get('Id', 0))
        except ValueError:
            continue # 没有有效 ID 的数据直接跳过
            
        try:
            score = int(row.get('Score', 0))
        except ValueError:
            score = 0

        # 组装数据模型
        item = ImageItem(
            id=post_id,
            site=str(row.get('Site', 'Unknown')),
            created_at=str(row.get('Posted', '')),
            artist=str(row.get('Artist', 'Unknown')),
            rating=str(row.get('Rating', '')),
            score=score,
            width=width,
            height=height,
            url=str(row.get('File_URL', '')),
            tags=str(row.get('Tags', ''))
        )
        items_to_save.append(item)

    print(f"成功解析 {len(items_to_save)} 条数据，准备导入数据库...")
    
    # 2. 实例化数据库管理器 (会自动建表)
    db_manager = DBManager(DB_PATH)
    
    # 3. 分批次导入 (每批 1000 条)，防止内存卡死
    batch_size = 1000
    for i in range(0, len(items_to_save), batch_size):
        batch = items_to_save[i : i + batch_size]
        # 直接复用之前写好的入库逻辑，它会自动处理多表映射和去重！
        db_manager.save_items(batch)
        print(f"进度: 已导入 {min(i + batch_size, len(items_to_save))} / {len(items_to_save)} ...")
        
    print("历史数据全部迁移至 SQLite 数据库！")

if __name__ == "__main__":
    import_csv_to_db()