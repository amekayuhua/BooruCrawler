from crawlers.base import BaseBoard
from crawlers.Gelbooru import Gelbooru
from crawlers.Danbooru import Danbooru
from core.storage import DataManager
from core.downloader import Downloader
from core.roster import ArtistRoster
from core.database import DBManager
import config
from typing import Type


class CrawlerFactory:
    CRAWLERS: dict[str, Type[BaseBoard]] = {
        'gelbooru': Gelbooru,
        "danbooru": Danbooru
    }
    
    @staticmethod
    def get_crwaler(site: str) -> BaseBoard:
        crawler_type = CrawlerFactory.CRAWLERS.get(site.lower())
        if not crawler_type:
            supported = ", ".join(sorted(CrawlerFactory.CRAWLERS))
            raise ValueError(f"Invalid site: {site!r}. Supported: {supported}")
        return crawler_type(api_key=config.API["api_key"], user_id=config.API["user_id"], headers=config.HEADERS, proxy=config.PROXY)

def main():
    # 导入配置 ------------------------------------------------------------------
    # 网站接口
    headers = config.HEADERS
    site = config.SITE
    proxy = config.PROXY

    # 关键词
    base_tags = config.SEARCH_TAGS
    artist = config.ARTIST_NAME
    rating = config.RATING
    sort_by = config.SORT_BY
    desc = config.DESCENDING

    # 文件位置
    data_output_path = config.DATA_OUTPUT_PATH
    image_output_path = config.IMAGES_OUTPUT_PATH
    database_path = config.DATABASE_PATH

    # 保存选项
    save_data = config.SAVE_DATA
    download_images = config.DOWNLOAD_IMAGES
    database = config.DATABASE
    word_cloud = config.WORDCLOUD
    # --------------------------------------------------------------------------

    # 实例化
    crawler = CrawlerFactory.get_crwaler(site=site)
    # 清洗标签（根据本站点规则）
    # 这里是用于保存文件的标签
    file_tags = crawler.get_safe_tag_name(base_tags)
    # 这里是用于注入apiurl的标签
    final_tags = crawler.assemble_tags(base_tags=base_tags, artist=artist, rating=rating, sort_by=sort_by, desc=desc)

    data_manager = DataManager(file_path=data_output_path, artist=artist, tags=file_tags)
    downloader = Downloader(save_path=image_output_path, artist=artist, tags=file_tags, headers=headers, proxy=proxy)

    print(f"正在检索关键词: {final_tags} ")
    total_count = crawler.get_total_count(final_tags)

    if total_count:
        roster_path = data_output_path + rf"\artists_roster.txt"
        roster = ArtistRoster(filepath=roster_path)
        if artist:
            roster.add(artist)

        user_input = input("请输入想要获取的数量 (输入 'all' 下载全部): ")
        if user_input.lower() == "all":
            final_limit = total_count
        else:
            final_limit = min(int(user_input), total_count)

        if final_limit == 0:
            print("取消下载。")
            return

        # 1. 启动爬虫获取初始数据
        image_items = crawler.start_crawling(final_tags, final_limit)

        # 2. 将数据扔给 Roster 进行画师标注补全
        image_items = roster.assign_artists(image_items)

        if save_data:
            data_manager.save_as_csv(image_items)
            data_manager.save_to_summary_csv(image_items)
            if word_cloud:
                data_manager.generate_wordcloud()
                
        if database:
            db_manager = DBManager(database_path)
            db_manager.save_items(image_items)

        if download_images:
            downloader.download(image_items)

# 启动爬虫
main()
# python run.py
