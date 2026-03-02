from .base import BaseBoard
from core.models import ImageItem
import re
import requests
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Gelbooru(BaseBoard):
    def __init__(self, api_key=None, user_id=None, proxy=None, headers=None):
        super().__init__(api_key, user_id, proxy, headers)
        self.base_url = "https://gelbooru.com/index.php?page=dapi&s=post&q=index"
        
    @staticmethod
    def get_safe_tag_name(tags: str) -> str:
        if not tags:
            return ""

        safe_name = tags.lower().strip()
        safe_name = safe_name.replace(' ', '_')
        safe_name = safe_name.replace('*', '').replace('?', '')

        safe_name = re.sub(r'_+', '_', safe_name)
        safe_name = safe_name.strip(' ._')

        if len(safe_name) > 100:
            safe_name = safe_name[:100]

        return safe_name

    def _get_sort_string(self, sort_by, desc):
        """返回该站点的排序语句（sort:score:desc等）"""
        if not sort_by:
            return ""
        return f"sort:{sort_by}:{desc}"

    def _build_params(self, tags, page, limit):
        """组装Gelbooru API参数"""
        params = {
            "tags": tags,
            "user_id": self.user_id,
            "api_key": self.api_key,
            "json": 1,
            "limit": limit,
            "pid": page
        }
        logger.debug(f"构建参数: page={page}, limit={limit}, tags={tags[:30]}...")
        return params
    
    def _parse_json_list(self, json_data):
        """解析JSON数据（Gelbooru返回在post键中）"""
        if isinstance(json_data, dict):
            return json_data.get("post", [])
        return []

    def _get_count(self, response_json):
        """从响应中提取图片总数"""
        if "@attributes" in response_json:
            count = int(response_json["@attributes"]["count"])
            if count != 0:
                logger.info(f"获取总数: {count} 张图片")
                return count
            else:
                logger.info("未检索到图片")
        return 0
    
    def get_total_count(self, tags) -> int:
        """发送探测请求，获取搜索结果总数量"""
        req_proxies = None
        if self.proxy and isinstance(self.proxy, str):
            req_proxies = {
                "http": self.proxy,
                "https": self.proxy
            }
        
        probe_params = self._build_params(tags, page=0, limit=1)
        logger.debug(f"获取总数: base_url?tags={tags[:30]}...")
        
        try:
            response = requests.get(self.base_url, params=probe_params, proxies=req_proxies, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            return self._get_count(response.json())
        except Exception as e:
            logger.error(f"获取总数失败: {e}")
            return 0

    def _normalize_data(self, raw_post):
        """将Gelbooru的原始数据转换为标准ImageItem"""
        created_at = raw_post.get("created_at", "")
        formatted_date = created_at
        if created_at:
            try:
                dt = datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")
                formatted_date = dt.strftime("%Y-%m-%d")
            except ValueError:
                logger.debug(f"[{raw_post.get('id')}] 时间解析失败: {created_at}")
        
        logger.debug(f"[{raw_post.get('id')}] 转换: {raw_post.get('rating')} {raw_post.get('width')}x{raw_post.get('height')}")
        
        return ImageItem(
            id=raw_post.get("id"),
            url=raw_post.get("file_url"),
            tags=raw_post.get("tags"),
            rating=raw_post.get("rating"),
            width=raw_post.get("width"),
            height=raw_post.get("height"),
            source=raw_post.get("source"),
            created_at=formatted_date,
            score=raw_post.get("score"),
            site="Gelbooru"
        )