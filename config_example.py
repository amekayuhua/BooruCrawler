# config.py的示例 实际使用时请将该文件改名为config.py


# 网络相关 ---------------------------------------------------------

# 代理端口
PROXY = "your_proxy"


# 站点相关 ---------------------------------------------------------
# 只保留使用的网站 不使用的网站全部注释掉

# gelbooru
SITE = "gelbooru"
API = {
    "user_id": your_user_id, # type: ignore (int类型)
    "api_key": "your_api_key"
}

# 每次运行生成一个随机的浏览器身份
from fake_useragent import UserAgent
ua = UserAgent()
HEADERS = {
    "User-Agent": ua.random,
    "Referer": "https://gelbooru.com/"
}

# danbooru
# SITE = "danbooru"
# API = {
#     "api_key": "your_api_key",
#     "user_id": "your_user_id"
# }
# 将 User-Agent 改为 项目名 + 你的用户名 的格式
# HEADERS = {"User-Agent": 'BooruCrawler (by your_user_id)'}


# 检索相关 ---------------------------------------------------------

# 排序
SORT_BY = "id" # "updated", "score", "id"(default)

# 正序or倒叙
DESCENDING = "desc"

# 级别
RATING = "general" # "sensitive", "questionable", "explicit"

# 画师名（选填）
ARTIST_NAME = ""

# 标签 （选填）
SEARCH_TAGS = ""

# 停用词（选填）
STOP_WORDS = {
    "your_stop_words"
}


# 保存相关 ---------------------------------------------------------

# 保存csv数据
SAVE_DATA = True # bool

# csv保存地址
DATA_OUTPUT_PATH = "data_output_path"

# 下载图片
DOWNLOAD_IMAGES = True # bool

# 图片文件夹保存地址
IMAGES_OUTPUT_PATH = "images_output_path" 

# 保存到数据库
DATABASE = True # bool

# 数据库保存地址
DATABASE_PATH = "database_path"

# 是否生成词云图
WORDCLOUD = True # bool