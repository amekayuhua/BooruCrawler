from dataclasses import dataclass, field
import os
from typing import Optional

@dataclass
class ImageItem:
    # --- 1. 基础数据字段 ---
    id: int
    url: str
    rating: str
    tags: str
    width: int
    height: int
    source: str = ""
    created_at: str = ""
    score: int = 0
    site: str = ""
    
    # 扩展字段：有些网站 URL 里不带后缀，需要单独传进来，或者自动推导
    _extension: Optional[str] = field(default=None, repr=False)

    @property
    def extension(self) -> str:
        """
        自动从 URL 获取后缀，如果获取不到则默认为 .jpg
        """
        if self._extension:
            return self._extension
        
        if self.url:
            ext = os.path.splitext(self.url)[-1]
            # 有些 url 后面带参数，比如 .jpg?v=123，需要清洗
            if '?' in ext:
                ext = ext.split('?')[0]
            if ext:
                return ext.lower()
        
        return ".jpg"

    @property
    def filename(self) -> str:
        """
        生成标准文件名：ID + 后缀
        例如: 123456.jpg
        """
        return f"{self.id}{self.extension}"

    @property
    def is_video(self) -> bool:
        """是否为视频文件"""
        return self.extension in ['.mp4', '.webm', '.gif']

    @property
    def is_explicit(self) -> bool:
        """是否为 R18 内容"""
        # 兼容不同网站的写法 (e, explicit, sx)
        return self.rating.lower() in ['explicit', 'e', 'sx']

    def to_dict(self, artist="") -> dict:
        """
        导出为字典，用于保存 CSV
        对应你 main.py 里 save_data 需要的格式
        """
        row = {
            "Id": self.id,
            "Site": self.site,
            "Posted": self.created_at,
            "Artist": "Unknown",
            "Rating": self.rating,
            "Score": self.score,
            "Size": f"{self.width}x{self.height}",
            "File_URL": self.url,
            "Tags": self.tags
        }
        
        if artist:
            row["Artist"] = artist
        
        return row