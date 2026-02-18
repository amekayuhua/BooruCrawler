from .base import BaseBoard
from core.models import ImageItem
import re
import requests
from datetime import datetime

class Gelbooru(BaseBoard):
    def __init__(self, api_key=None, user_id=None, proxy=None, headers=None):
        super().__init__(api_key, user_id, proxy, headers)
        self.base_url = "https://gelbooru.com/index.php?page=dapi&s=post&q=index"
        
    @staticmethod
    def get_safe_tag_name(tags: str) -> str:
        if not tags:
            return ""

        # 1. 统一转小写
        safe_name = tags.lower().strip()

        # 2. Gelbooru 特有方言处理
        safe_name = safe_name.replace(' ', '_')
        safe_name = safe_name.replace('*', '').replace('?', '')

        # 4. 美化 (去重下划线，去首尾点符号)
        safe_name = re.sub(r'_+', '_', safe_name)
        safe_name = safe_name.strip(' ._')

        # 5. 长度截断 (防止文件名溢出)
        if len(safe_name) > 100:
            safe_name = safe_name[:100]

        return safe_name

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
    
    def get_total_count(self, tags) -> int:
        """
        只负责发送探测包，返回搜索结果的总数量
        """
        req_proxies = None
        if self.proxy and isinstance(self.proxy, str):
            req_proxies = {
                "http": self.proxy,
                "https": self.proxy
            }
        # 构造 limit=1 的探测参数
        probe_params = self._build_params(tags, page=0, limit=1)
        try:
            # 发送请求
            response = requests.get(self.base_url, params=probe_params, proxies=req_proxies, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # 调用子类解析 count
            return self._get_count(response.json())
        except Exception as e:
            print(f"请求失败: {e}")
            return 0

    def _normalize_data(self, raw_post):
        # Gelbooru 特有的字段映射
        # --- 时间格式化 ---
        # 原始: "Thu Feb 05 08:16:25 -0600 2026"
        created_at = raw_post.get("created_at", "")
        formatted_date = created_at
        if created_at:
            try:
                # 解析 Gelbooru 的特殊时间格式
                dt = datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")
                # 转为 YYYY-MM-DD
                formatted_date = dt.strftime("%Y-%m-%d")
            except ValueError:
                # 如果解析失败（比如格式变了），保留原样或记录错误
                pass
            
        return ImageItem(
            id=raw_post.get("id"),
            url=raw_post.get("file_url"),
            tags=raw_post.get("tags"),
            rating=raw_post.get("rating"),
            width=raw_post.get("width"),
            height=raw_post.get("height"),
            source=raw_post.get("source"),
            created_at=formatted_date, # 使用清洗后的时间
            score=raw_post.get("score"),
            site="Gelbooru"
        )