import os
import sys

# 将项目根目录加入系统路径，以便能导入 core 模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.roster import ArtistRoster

# ================= 配置区域 =================
# 配置你的名单 txt 和 汇总数据 csv 的路径
ROSTER_PATH = r"D:\pyworks\BooruCrawler\output\datasets"
CSV_PATH = r"D:\pyworks\BooruCrawler\output\datasets\datas.csv"
# ==========================================

def run_cleaner():
    print("启动历史数据清洗工具...")
    
    # 1. 实例化花名册 (此时它会自动加载本地 txt 里的名字)
    roster = ArtistRoster(filepath=ROSTER_PATH)
    
    print(f"当前画师知识库已收录 {len(roster.artists)} 位画师。")
    
    # 2. 执行清洗
    roster.clean_summary_dataset(CSV_PATH)

if __name__ == "__main__":
    run_cleaner()