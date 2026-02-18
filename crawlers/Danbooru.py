from .base import BaseBoard
from core.models import ImageItem
import re
import requests

class Danbooru(BaseBoard):
    def __init__(self, api_key=None, user_id=None, proxy=None, headers=None):
        super().__init__(api_key, user_id, proxy, headers)
        # Danbooru 的标准 API 地址
        self.base_url = "https://danbooru.donmai.us/posts.json"

    def get_safe_tag_name(self, tags: str) -> str:
        """
        Danbooru 清洗规则：
        1. 空格转下划线
        2. 冒号转下划线 (Windows 不允许冒号)
        """
        if not tags: return "all"
        
        safe_name = tags.lower().strip()
        safe_name = safe_name.replace(' ', '_')
        safe_name = safe_name.replace(':', '_')
        
        # 移除通配符和非法字符
        safe_name = re.sub(r'[\*\?]', '', safe_name)
        safe_name = re.sub(r'[<>"\\/|]', '', safe_name)
        
        # 美化
        safe_name = re.sub(r'_+', '_', safe_name)
        return safe_name.strip(' ._')[:100]

    def _get_sort_string(self, sort_by, desc):
        """
        Danbooru 排序语法: order:score, order:rank 等
        """
        if not sort_by:
            return ""
        
        # 处理别名，防止 config 里写错了
        if sort_by == "updated": return "order:id" # 默认就是 id 倒序
        
        # 如果用户只写了 score，补全为 order:score
        if not sort_by.startswith("order:"):
            return f"order:{sort_by}"
            
        return sort_by

    def _build_params(self, tags, page, limit):
        """
        Danbooru 参数构造
        """
        params = {
            "tags": tags,
            "limit": limit,
            # 关键差异：Danbooru 页码从 1 开始，而你的循环通常从 0 开始
            "page": page + 1 
        }

        # 关键差异：Danbooru 验证身份用的是 "login" (用户名) 而不是 "user_id"
        if self.api_key and self.user_id:
            params["login"] = self.user_id 
            params["api_key"] = self.api_key
            
        return params
    
    def _parse_json_list(self, json_data):
        """
        Danbooru 直接返回列表，不需要拆包
        """
        if isinstance(json_data, list):
            return json_data
        return []
    
    def _get_count(self, json_data) -> int:
        """
        [实现父类抽象方法]
        从 /counts/posts.json 的返回数据中提取 count
        数据结构示例: {"counts": {"posts": 12345}}
        """
        try:
            count = int(json_data.get("counts", {}).get("posts", 0))
            print(f"检索到 {count} 张图片")
            return count
        except Exception as e:
            print(f"解析数量失败: {e}")
            return 0

    def get_total_count(self, tags) -> int:
        """
        [重写父类方法]
        Danbooru 必须请求专门的计数接口 /counts/posts.json
        """
        count_url = "https://danbooru.donmai.us/counts/posts.json"
        
        params = {"tags": tags}
        
        # 带上鉴权，防止因权限不足导致搜索结果不准确
        if self.api_key and self.user_id:
            params["login"] = self.user_id
            params["api_key"] = self.api_key

        req_proxies = None
        if self.proxy and isinstance(self.proxy, str):
            req_proxies = {"http": self.proxy, "https": self.proxy}

        try:
            
            response = requests.get(
                count_url, 
                params=params, 
                headers=self.headers, 
                proxies=req_proxies, 
                timeout=10
            )
            response.raise_for_status()
            
            # 关键点：这里调用上面写好的 _get_count 来解析数据
            return self._get_count(response.json())
            
        except Exception as e:
            print(f"获取数量请求失败: {e}")
            return 0

    def _normalize_data(self, raw_post):
        """
        字段清洗：Danbooru 的字段名和 Gelbooru 不太一样
        """
        # 有些特殊的帖子可能没有 file_url (比如被删除了，或者只有 large_file_url)
        url = raw_post.get("file_url") or raw_post.get("large_file_url")
        
        if not url:
            return None
        
        url = raw_post.get("file_url") or raw_post.get("large_file_url")
        if not url:
            return None

        # --- 1. 时间格式化 ---
        # 原始: "2026-02-11T12:48:23.792-05:00"
        # 这种 ISO 格式最简单，直接按 "T" 切割取前半部分即可
        created_at = raw_post.get("created_at", "")
        if created_at and "T" in created_at:
            created_at = created_at.split("T")[0]

        # --- 2. Rating 全称化 ---
        # 原始: "e", "q", "s", "g"
        rating_map = {
            "e": "explicit",
            "q": "questionable",
            "s": "sensitive",
            "g": "general"
        }
        raw_rating = raw_post.get("rating") or ""
        # 如果是简写就映射，找不到就用原值
        formatted_rating = rating_map.get(raw_rating, raw_rating)

        return ImageItem(
            id=raw_post.get("id"),
            url=url,
            # Danbooru 的 tags 是一个空格分隔的字符串 "tag1 tag2"
            tags=raw_post.get("tag_string", ""), 
            rating=formatted_rating,
            width=raw_post.get("image_width"),
            height=raw_post.get("image_height"),
            source=raw_post.get("source"),
            created_at=created_at, # 使用清洗后的时间
            score=raw_post.get("score"),
            site="Danbooru"
        )