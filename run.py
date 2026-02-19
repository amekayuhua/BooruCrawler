from crawlers.base import BaseBoard
from crawlers.Gelbooru import Gelbooru
from crawlers.Danbooru import Danbooru
from core.storage import DataManager
from core.downloader import Downloader
import config
from typing import Type
# from core.utils import


class CrawlerFActory:
    CRAWLERS: dict[str, Type[BaseBoard]] = {
        'gelbooru': Gelbooru,
        "danbooru": Danbooru
    }
    
    @staticmethod
    def get_crwaler(site: str) -> BaseBoard:
        crawler_type = CrawlerFActory.CRAWLERS.get(site.lower())
        if not crawler_type:
            supported = ", ".join(sorted(CrawlerFActory.CRAWLERS))
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

    # 保存选项
    save_data = config.SAVE_DATA
    download_images = config.DOWNLOAD_IMAGES
    word_cloud = config.WORDCLOUD
    # --------------------------------------------------------------------------

    # 实例化
    crawler = CrawlerFActory.get_crwaler(site=site)
    tags = crawler.get_safe_tag_name(base_tags)
    data_manager = DataManager(file_path=data_output_path, artist=artist, tags=tags)
    downloader = Downloader(save_path=image_output_path, artist=artist, tags=tags, headers=headers, proxy=proxy)

    final_tags = crawler.assemble_tags(base_tags=base_tags, artist=artist, rating=rating, sort_by=sort_by, desc=desc)

    print(f"正在检索关键词: {final_tags} ")
    total_count = crawler.get_total_count(final_tags)

    if total_count:
        user_input = input("请输入想要获取的数量 (输入 'all' 下载全部): ")
        if user_input.lower() == "all":
            final_limit = total_count
        else:
            final_limit = min(int(user_input), total_count)

        if final_limit == 0:
            print("取消下载。")
            return

        # image_items = crawler.fetch_posts(final_tags, final_limit)
        image_items = crawler.start_crawling(final_tags, final_limit)

        if save_data:
            data_manager.load_existing_ids()
            data_manager.save_as_csv(image_items)
            data_manager.save_to_summary_csv(image_items)
            if word_cloud:
                data_manager.generate_wordcloud()

        if download_images:
            downloader.download(image_items)

# 启动爬虫
main()
# python run.py
