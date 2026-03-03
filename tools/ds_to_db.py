import os
import sys
import pandas as pd
# from tqdm import tqdm
from rich.progress import (
    Progress, 
    SpinnerColumn, 
    TextColumn, 
    BarColumn, 
    TaskProgressColumn, 
    MofNCompleteColumn,
    TimeElapsedColumn
)
import logging

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from core.log_config import setup_global_logger, console
from core.database import DBManager
from core.models import ImageItem

logger = logging.getLogger(__name__)

# ================= 配置区域 =================
CSV_PATH = r"D:\pyworks\BooruCrawler\output\datasets\datas.csv"
DB_PATH = r"D:\pyworks\python数据处理\databases\booru_gallery.db"
# ==========================================

def get_total_lines(filepath):
    """快速获取文件的总行数"""
    logger.info("扫描文件总行数...")
    with open(filepath, 'rb') as f:
        total_lines = sum(1 for _ in f) - 1
    return total_lines

def import_csv_to_db():
    if not os.path.exists(CSV_PATH):
        logger.error(f"CSV 文件不存在: {CSV_PATH}")
        return

    total_rows = get_total_lines(CSV_PATH)
    logger.info(f"准备导入 {total_rows} 条数据")

    db_manager = DBManager(DB_PATH)
    chunk_size = 2500
    
    logger.info("开始流式导入数据...")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold green]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),  # 显示 2500/11699 这种格式
        TaskProgressColumn(),
        TimeElapsedColumn(),   # 显示已经耗费的时间
        console=console,       # 绑定全局控制台
        transient=False        # 迁移完成后保留进度条在屏幕上，方便看最终结果
    ) as progress:
        
        main_task = progress.add_task("数据迁移中...", total=total_rows)
    
        for chunk in pd.read_csv(CSV_PATH, chunksize=chunk_size):
            
            chunk = chunk.fillna('')
            batch_items = []
            
            for index, row in chunk.iterrows():
                size_str = str(row.get('Size', ''))
                width, height = 0, 0
                if 'x' in size_str:
                    try:
                        w_str, h_str = size_str.split('x', 1)
                        width = int(w_str)
                        height = int(h_str)
                    except ValueError:
                        pass
                
                try:
                    post_id = int(row.get('Id', 0))
                except ValueError:
                    continue
                    
                try:
                    score = int(row.get('Score', 0))
                except ValueError:
                    score = 0

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
                batch_items.append(item)
            
            db_manager.save_items(batch_items)
            # pbar.update(len(chunk))
            progress.update(main_task, advance=len(chunk))

    logger.info(f"已将 {CSV_PATH} 中的历史数据已全部安全迁移至 SQLite 数据库 {DB_PATH} 中")

if __name__ == "__main__":
    from core.log_config import setup_global_logger
    setup_global_logger()
    import_csv_to_db()