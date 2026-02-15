from abc import ABC, abstractmethod
import config
from core.models import ImageItem
import requests
import time



class BaseBoard(ABC):
    MAX_LIMIT = 100
    
    def __init__(self, api_key=None, user_id=None, proxy=None):
        self.api_key = api_key
        self.user_id = user_id
        self.proxy = proxy
        self.headers = config.HEADERS # 通用头
        # 不同的子类在初始化时设置自己的 base_url
        self.base_url = ""
        
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

        if base_tags: tags_list.append(base_tags)
        if artist:    tags_list.append(artist)
        if rating:    tags_list.append(f"rating:{rating}:desc")
        
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

    def fetch_posts(self, tags, limit_num="all"):
        """
        通用逻辑：
        1. 构造探测参数 (limit=1)
        2. 发请求，拿 count (调用子类的 _get_count)
        3. 决定下载多少
        4. 循环或一次性拉取所有数据
        5. 清洗数据 (调用子类的 _normalize_data)
        6. 返回 [ImageItem, ImageItem, ...]
        """
        probe_params = self._build_params(tags, page=0, limit=1)
        
        try:
            response = requests.get(self.base_url, params=probe_params, headers=self.headers)
            response.raise_for_status() # 检查 200 OK
            
            json_data = response.json() 
            
        except Exception as e:
            print(f"网络异常: {e}")
            return []

        total_count = self._get_count(json_data) 
        
        if total_count == 0:
            print(f"关键词 [{tags}] 未匹配到任何图片。")
            return []
        
        target_count = 0
        
        if str(limit_num).lower() == "all":
            target_count = total_count
        else:
            try:
                user_ask = int(limit_num)
                # 取“用户想要的”和“实际有的”较小值
                target_count = min(user_ask, total_count)
            except ValueError:
                print(f"无效的数量输入: {limit_num}，默认下载 10 张")
                target_count = min(10, total_count)

        print(f"根据要求将下载 {target_count} 张。")
                
        images = []
        page = 0

        print(f"开始批量获取元数据...")

        # 只要手里的图还没凑够，就继续循环
        while len(images) < target_count:
            
            # 4.1 计算这一勺挖多少？
            # 公式：还没满足的数量 vs 汤勺的最大容量 (MAX_LIMIT)
            remaining = target_count - len(images)
            current_limit = min(remaining, self.MAX_LIMIT)
            
            # 4.2 填表 (调用子类的 _build_params)
            # 注意：这里我们只传“第几页(page)”，子类自己决定是叫 pid 还是 page
            params = self._build_params(tags, page, current_limit)
            
            try:
                # 4.3 发请求
                response = requests.get(self.base_url, params=params, headers=self.headers, timeout=10)
                
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
                
                print(f"  > 进度: {len(images)} / {target_count}")

                # 4.6 翻页 & 休息 (防封号)
                page += 1
                time.sleep(0.5) 
                
            except Exception as e:
                print(f"[错误] 抓取过程中断: {e}")
                break
        
        # 双重保险：虽然循环条件控制了，但返回前最好截断一下，确保不多不少
        return images[:target_count]