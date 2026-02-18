from abc import ABC, abstractmethod
from core.models import ImageItem
import requests
import time
from typing import List


class BaseBoard(ABC):
    MAX_LIMIT = 100
    
    def __init__(self, api_key=None, user_id=None, proxy=None, headers=None):
        self.api_key = api_key
        self.user_id = user_id
        self.proxy = proxy
        self.headers = headers
        self.base_url = ""
    
    @abstractmethod
    def get_safe_tag_name(self, tags: str) -> str:
        """
        子类必须实现：
        根据本站点的搜索语法特性，将 tags 清洗为合法的文件系统名称。
        """
        pass
        
    @abstractmethod
    def _get_sort_string(self, sort_by, desc) -> str:
        """
        抽象方法：强制子类告诉我，你们家的排序语法长什么样？
        """
        pass
    
    def assemble_tags(self, base_tags, artist, rating, sort_by, desc):
        """
        通用标签组装逻辑。
        子类如果规则不一样（比如 D 站的排序），需要重写这个方法。
        """
        tags_list = []

        if artist:    tags_list.append(artist)
        if base_tags: tags_list.append(base_tags)
        if rating:    tags_list.append(f"rating:{rating}")
        
        # 留给子类去处理 unique 的部分
        specific_part = self._get_sort_string(sort_by, desc) 
        if specific_part:
            tags_list.append(specific_part)
            
        return " ".join(tags_list)

    @abstractmethod
    def _get_count(self, params) -> int:
        """子类必须实现：如何从响应中提取图片总数"""
        pass
    
    @abstractmethod
    def _build_params(self, tags, page, limit) -> dict:
        """子类必须实现：如何组装 URL 参数"""
        pass
    
    @abstractmethod
    def _parse_json_list(self, json_data) -> list:
        '''子类需实现对不同json的解析'''
        pass

    @abstractmethod
    def _normalize_data(self, raw_post) -> ImageItem:
        """子类必须实现：把网站乱七八糟的 JSON 字段清洗成标准的 ImageItem"""
        pass
    
    @abstractmethod
    def get_total_count(self, tags) -> int:
        """
        只负责发送探测包，返回搜索结果的总数量
        """
        pass
    
    def fetch_posts(self, tags: str, limit_num: int) -> List[ImageItem]:
 
        images = []
        page = 0
        target_count = limit_num  # 这里直接接收用户的最终决定

        print(f"收到指令，准备下载 {target_count} 张图片元数据...")

        # 只要手里的图还没凑够，就继续循环
        while len(images) < target_count:
            
            current_limit = self.MAX_LIMIT
            params = self._build_params(tags, page, current_limit)
            
            req_proxies = None
            if self.proxy and isinstance(self.proxy, str):
                req_proxies = {
                    "http": self.proxy,
                    "https": self.proxy
                }
                
            try:
                # 4.3 发请求
                response = requests.get(self.base_url, params=params, headers=self.headers, proxies=req_proxies, timeout=10)
                
                if response.status_code != 200:
                    print(f"[警告] 第 {page} 页请求失败，状态码: {response.status_code}")
                    break # 遇到错就停，或者你可以写重试逻辑
                
                json_data = response.json()
                
                # 4.4 提取列表 (关键点！)
                # Gelbooru 返回的是 {"post": [...]}, Danbooru 返回的是 [...]
                # 我们需要一个新方法 _parse_json_list 来屏蔽这个差异
                raw_posts = self._parse_json_list(json_data)
                
                if not raw_posts:
                    print(f"第 {page} 页是空的，看来是到底了。")
                    break
                
                # 4.5 清洗数据 (Raw Dict -> ImageItem)
                for raw_post in raw_posts:
                    # 调用子类的清洗逻辑
                    item = self._normalize_data(raw_post)
                    # 只有当 item 有效（比如有 url）时才收录
                    if item:
                        images.append(item)
                
                display_count = min(len(images), target_count)
                print(f"  > 进度: {display_count} / {target_count}")

                # 4.6 翻页 & 休息 (防封号)
                page += 1
                time.sleep(0.2) 
                
            except Exception as e:
                print(f"[错误] 抓取过程中断: {e}")
                break
        
        # 双重保险：虽然循环条件控制了，但返回前最好截断一下，确保不多不少
        return images[:target_count]