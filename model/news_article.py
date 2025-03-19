from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class NewsArticle:
    """新闻文章数据模型"""
    title: str
    author: str
    published_date: datetime
    content: str
    html_content: str
    url: str
    source: str
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    keyword: Optional[str] = None  # 添加关键词字段，用于存储搜索关键词 