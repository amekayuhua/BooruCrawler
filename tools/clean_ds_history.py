import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.roster import ArtistRoster
import logging

logger = logging.getLogger(__name__)


# ================= 配置区域 =================
# 配置画师名单 txt 和 汇总数据 csv 的路径
ROSTER_PATH = r"D:\pyworks\BooruCrawler\output\datasets\artists_roster.txt"
CSV_PATH = r"D:\pyworks\BooruCrawler\output\datasets\datas.csv"
# ==========================================

def run_cleaner():
    logger.info("启动历史数据清洗工具...")
    roster = ArtistRoster(filepath=ROSTER_PATH)
    logger.info(f"当前画师知识库已收录 {len(roster.artists)} 位画师。")
    
    roster.clean_summary_dataset(CSV_PATH)

if __name__ == "__main__":
    from core.log_config import setup_global_logger
    setup_global_logger()
    run_cleaner()