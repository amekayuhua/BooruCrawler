import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import DBManager, Artist
from core.roster import ArtistRoster
import logging

logger = logging.getLogger(__name__)

# ================= 配置区域 =================
DB_PATH = r"D:\pyworks\python数据处理\databases\booru_gallery.db"
ROSTER_PATH = r"D:\pyworks\BooruCrawler\output\datasets\artists_roster.txt"
# ==========================================

def clean_database():
    logger.info("开始清洗数据库未知画师数据")
    roster = ArtistRoster(ROSTER_PATH)
    if not roster.artists:
        logger.warning("本地画师名单为空")
        return

    db_manager = DBManager(DB_PATH)
    session = db_manager.Session()
    updated_count = 0

    try:
        unknown_artist = session.query(Artist).filter_by(name='Unknown').first()
        if not unknown_artist:
            logger.info("数据库中没有未知画师")
            return

        unknown_images = unknown_artist.images

        logger.info(f"发现 {len(unknown_images)} 张未匹配画师的图片，开始匹配...")

        for img in unknown_images:
            tag_names = [tag.name for tag in img.tags]
            tags_str = " ".join(tag_names)

            matched_artists = roster.extract_artists(tags_str)

            if matched_artists:
                img.artists.remove(unknown_artist)
                
                for a_name in matched_artists:
                    real_artist = db_manager._get_or_create(session, Artist, name=a_name)
                    if real_artist not in img.artists:
                        img.artists.append(real_artist)
                
                updated_count += 1

        session.commit()
        logger.info(f"成功匹配 {updated_count} 张图片的画师")

    except Exception as e:
        session.rollback()
        logger.error(f"清洗过程出错: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    from core.log_config import setup_global_logger
    setup_global_logger()
    clean_database()