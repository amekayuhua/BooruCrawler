# 需要爬取的网站api
API_URL = "https://gelbooru.com/index.php?page=dapi&s=post&q=index"

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

SORT_BY = '' # 可选值: 'updated', 'score', 'id'(default)

DESCENDING = 'desc'

RATING = 'explicit'

ARTIST_NAME = 'cian_yo'

SEARCH_TAGS = ''

API = {
    'user_id': 1914481,
    'api_key': '295b1d7020cd90cf84cbe41a81e38b607a2ef866183ba59eca647bdc74661ced546d1b3e4e4f42d0c284f18d0098d8eb8a6778264ea32e49a0f0880d253a31a1'
}

SAVE_DATA = False

DATA_OUTPUT_PATH = r'D:\pyworks\python数据处理\自制小工具\图站爬虫\datasets'

DOWNLOAD_IMAGES = False

IMAGES_OUTPUT_PATH = r'D:\pyworks\python数据处理\自制小工具\图站爬虫\images'

PROXY = "http://127.0.0.1:7890"