from crawlers.base import BaseBoard
from crawlers.Gelbooru import Gelbooru
from core.storage import DataManager
import config
from typing import Type
# from core.utils import


class CrawlerFActory:
    CRAWLERS: dict[str, Type[BaseBoard]] = {
        'gelbooru': Gelbooru
    }
    
    @staticmethod
    def get_crwaler(site: str) -> BaseBoard:
        crawler_type = CrawlerFActory.CRAWLERS.get(site.lower())
        if not crawler_type:
            supported = ", ".join(sorted(CrawlerFActory.CRAWLERS))
            raise ValueError(f"Invalid site: {site!r}. Supported: {supported}")
        return crawler_type(api_key=config.API["api_key"], user_id=config.API["user_id"])
    
def main():
    # 网站接口
    api_url = config.API_URL
    header = config.HEADERS
    user_id = config.API["user_id"]
    api_key = config.API["api_key"]
    
    # 关键词
    base_tags = config.SEARCH_TAGS
    artist = config.ARTIST_NAME
    full_tags = config.FULL_TAGS
    rating = config.RATING
    sort_by = config.SORT_BY
    desc = config.DESCENDING
    
    # 文件位置
    data_output_path = config.DATA_OUTPUT_PATH
    image_output_path = config.IMAGES_OUTPUT_PATH
    
    crawler = CrawlerFActory.get_crwaler(config.SITE)
    data_manager = DataManager(file_path=data_output_path, full_tags=full_tags)

    final_tags = crawler.assemble_tags(base_tags=base_tags,
                                       artist=artist,
                                       rating=rating,
                                       sort_by=sort_by,
                                       desc=desc
                                       )
    
    print(f"正在检索关键词: {final_tags} ...")
    total_count = crawler.get_total_count(final_tags) # 调用新方法
    
    if total_count:
        user_input = input("请输入想要获取的数量 (输入 'all' 下载全部): ")
        
        if user_input.lower() == "all":
            final_limit = total_count
        else:
            # 这里做 min 取值，防止用户要 10000 但实际只有 50
            final_limit = min(int(user_input), total_count)

        if final_limit == 0:
            print("取消下载。")
            return

        image_items = crawler.fetch_posts(final_tags, final_limit)
        
        if config.SAVE_DATA:
            data_manager.load_existing_ids()
            data_manager.save_as_csv(image_items)
        
main()