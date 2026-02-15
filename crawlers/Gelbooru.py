from .base import BaseBoard
from core.models import ImageItem

class Gelbooru(BaseBoard):
    def __init__(self, api_key=None, user_id=None, proxy=None):
        super().__init__(api_key, user_id, proxy)
        self.base_url = "https://gelbooru.com/index.php?page=dapi&s=post&q=index"

    def _get_sort_string(self, sort_by, desc):
        if not sort_by:
            return ""
        # Gelbooru 语法: sort:score:desc
        # 注意：这里假设默认都是降序 desc，如果需要精细控制，可以将 desc 作为一个参数传进来
        return f"sort:{sort_by}:{desc}"

    def _build_params(self, tags, page, limit):
        # Gelbooru 特有的参数构造
        return {
            "tags": tags,
            "user_id": self.user_id,
            "api_key": self.api_key,
            "json": 1,
            "limit": limit,
            "pid": page
        }
    
    def _parse_json_list(self, json_data):
        """
        Gelbooru 的特殊处理：
        它的 JSON 不是直接的列表，而是包裹在 "post" 键下面的。
        """
        # 1. 检查数据是不是字典 (盒子)
        if isinstance(json_data, dict):
            # 2. 尝试拿 "post" 里面的东西，如果拿不到就返回空列表
            return json_data.get("post", [])
        
        # 3. 如果根本不是字典（比如是个空列表），直接返回空
        return []

    def _get_count(self, response_json):
        # Gelbooru 特有的 count 获取逻辑 (你现在的逻辑)
        if "@attributes" in response_json:
            count = int(response_json["@attributes"]["count"])
            print(f"检索到 {count} 张图片")
            return count
        return 0

    def _normalize_data(self, raw_post):
        # Gelbooru 特有的字段映射
        return ImageItem(
            id=raw_post.get("id"),
            url=raw_post.get("file_url"),
            tags=raw_post.get("tags"),
            rating=raw_post.get("rating"),
            width=raw_post.get("width"),
            height=raw_post.get("height"),
            source=raw_post.get("source"),
            created_at=raw_post.get("created_at"),
            score=raw_post.get("score")
        )