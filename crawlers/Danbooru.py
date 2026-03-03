from .base import BaseBoard
from core.models import ImageItem
import re
import requests
import logging 

logger = logging.getLogger(__name__)

class Danbooru(BaseBoard):
    def __init__(self, api_key=None, user_id=None, proxy=None, headers=None):
        super().__init__(api_key, user_id, proxy, headers)
        self.base_url = "https://danbooru.donmai.us/posts.json"

    def get_safe_tag_name(self, tags: str) -> str:
        """清洗标签为合法的文件名（空格转下划线，移除冒号和特殊字符）"""
        if not tags: return "all"
        
        safe_name = tags.lower().strip()
        safe_name = safe_name.replace(' ', '_')
        safe_name = safe_name.replace(':', '_')
        
        safe_name = re.sub(r'[\*\?]', '', safe_name)
        safe_name = re.sub(r'[<>"\\/|]', '', safe_name)
        
        safe_name = re.sub(r'_+', '_', safe_name)
        return safe_name.strip(' ._')[:100]

    def _get_sort_string(self, sort_by, desc):
        """返回该站点的排序语句（order:score, order:rank等）"""
        if not sort_by:
            return ""
        
        if sort_by == "updated": 
            return "order:id"
        
        if not sort_by.startswith("order:"):
            return f"order:{sort_by}:{desc}"
            
        return sort_by

    def _build_params(self, tags, page, limit):
        """组装Danbooru API参数"""
        params = {
            "tags": tags,
            "limit": limit,
            "page": page + 1  # Danbooru页码从1开始
        }

        if self.api_key and self.user_id:
            params["login"] = self.user_id 
            params["api_key"] = self.api_key
            
        logger.debug(f"构建参数: page={page+1}, limit={limit}, tags={tags[:30]}...")
        return params
    
    def _parse_json_list(self, json_data):
        """解析JSON数据（Danbooru直接返回列表）"""
        if isinstance(json_data, list):
            return json_data
        return []
    
    def _get_count(self, json_data) -> int:
        """从计数接口返回的数据中提取图片总数"""
        try:
            count = int(json_data.get("counts", {}).get("posts", 0))
            logger.info(f"获取总数: {count} 张图片/视频信息")
            return count
        except Exception as e:
            logger.error(f"解析总数失败: {e}")
            return 0

    def get_total_count(self, tags) -> int:
        """查询Danbooru的计数接口获取搜索结果总数"""
        count_url = "https://danbooru.donmai.us/counts/posts.json"
        
        params = {"tags": tags}
        
        if self.api_key and self.user_id:
            params["login"] = self.user_id
            params["api_key"] = self.api_key

        req_proxies = None
        if self.proxy and isinstance(self.proxy, str):
            req_proxies = {"http": self.proxy, "https": self.proxy}

        logger.debug(f"获取总数: {count_url}?tags={tags[:30]}...")
        try:
            response = requests.get(
                count_url, 
                params=params, 
                headers=self.headers, 
                proxies=req_proxies, 
                timeout=10
            )
            response.raise_for_status()
            
            return self._get_count(response.json())
            
        except Exception as e:
            logger.error(f"获取总数失败: {e}")
            return 0

    def _normalize_data(self, raw_post):
        """将Danbooru的原始数据转换为标准ImageItem"""
        url = raw_post.get("file_url") or raw_post.get("large_file_url")
        
        if not url:
            logger.warning(f"[{raw_post.get('id')}] 缺少URL，跳过")
            return None

        created_at = raw_post.get("created_at", "")
        if created_at and "T" in created_at:
            created_at = created_at.split("T")[0]

        rating_map = {
            "e": "explicit",
            "q": "questionable",
            "s": "sensitive",
            "g": "general"
        }
        raw_rating = raw_post.get("rating") or ""
        formatted_rating = rating_map.get(raw_rating, raw_rating)

        # logger.debug(f"[{raw_post.get('id')}] 转换: {formatted_rating} {raw_post.get('image_width')}x{raw_post.get('image_height')}")
        
        return ImageItem(
            id=raw_post.get("id"),
            url=url,
            tags=raw_post.get("tag_string", ""), 
            rating=formatted_rating,
            width=raw_post.get("image_width"),
            height=raw_post.get("image_height"),
            source=raw_post.get("source"),
            created_at=created_at,
            score=raw_post.get("score"),
            site="Danbooru",
            artist=raw_post.get("tag_string_artist", "")
        )