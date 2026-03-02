from dataclasses import dataclass, field
import os
from typing import Optional

@dataclass
class ImageItem:
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
    artist: str = ""
    
    _extension: Optional[str] = field(default=None, repr=False)

    @property
    def extension(self) -> str:
        """从URL自动获取文件后缀，如果获取失败则默认为.jpg"""
        if self._extension:
            return self._extension
        
        if self.url:
            ext = os.path.splitext(self.url)[-1]
            # URL参数清洗：.jpg?v=123 -> .jpg
            if '?' in ext:
                ext = ext.split('?')[0]
            if ext:
                return ext.lower()
        
        return ".jpg"

    @property
    def filename(self) -> str:
        """生成标准文件名格式：ID + 后缀（如：123456.jpg）"""
        return f"{self.id}{self.extension}"

    @property
    def is_video(self) -> bool:
        """判断是否为视频文件"""
        return self.extension in ['.mp4', '.webm', '.gif']

    @property
    def is_explicit(self) -> bool:
        """判断是否为R18内容"""
        return self.rating.lower() in ['explicit', 'e', 'sx']

    def to_dict(self, artist="") -> dict:
        """导出为字典用于CSV保存"""
        final_artist = self.artist or artist or "Unknown"
        
        row = {
            "Id": self.id,
            "Site": self.site,
            "Posted": self.created_at,
            "Artist": final_artist,
            "Rating": self.rating,
            "Score": self.score,
            "Size": f"{self.width}x{self.height}",
            "File_URL": self.url,
            "Tags": self.tags
        }
        
        return row