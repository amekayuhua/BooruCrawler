# tools/clean_db_history.py
import os
import sys

# 将项目根目录加入系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import DBManager, Image, Artist
from core.roster import ArtistRoster

# ================= 配置区域 =================
DB_PATH = r"D:\pyworks\python数据处理\sql_practices\booru_gallery.db"
ROSTER_PATH = r"D:\pyworks\BooruCrawler\output\datasets\artists_roster.txt"
# ==========================================

def clean_database():
    print("启动数据库历史数据清洗...")
    roster = ArtistRoster(ROSTER_PATH)
    if not roster.artists:
        print("本地画师名单为空，无法进行清洗。")
        return

    db_manager = DBManager(DB_PATH)
    session = db_manager.Session()
    updated_count = 0

    try:
        # 1. 找到数据库里名字叫 'Unknown' 的那个画师对象
        unknown_artist = session.query(Artist).filter_by(name='Unknown').first()
        if not unknown_artist:
            print("数据库中没有 Unknown 画师，无需清洗。")
            return

        # 2. 找到所有属于 'Unknown' 画师的图片
        unknown_images = unknown_artist.images

        print(f"找到 {len(unknown_images)} 张未知画师的图片，正在尝试匹配...")

        for img in unknown_images:
            # 提取这张图在数据库里的所有标签名字
            tag_names = [tag.name for tag in img.tags]
            tags_str = " ".join(tag_names)

            # 让名单去识别这些标签
            matched_artists = roster.extract_artists(tags_str)

            if matched_artists:
                # 识别成功！将这张图从 Unknown 的名下移除
                img.artists.remove(unknown_artist)
                
                # 为这张图绑定真正的主人
                for a_name in matched_artists:
                    # 使用我们之前写的去重创建方法
                    real_artist = db_manager._get_or_create(session, Artist, name=a_name)
                    if real_artist not in img.artists:
                        img.artists.append(real_artist)
                
                updated_count += 1

        # 统一保存更改
        session.commit()
        print(f"成功为 {updated_count} 张数据库图片重新匹配了画师。")

    except Exception as e:
        session.rollback()
        print(f"清洗过程发生错误: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    clean_database()