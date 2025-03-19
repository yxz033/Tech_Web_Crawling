from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class TrendItem:
    """趋势项目基础模型"""
    rank: int
    name: str
    description: str
    url: str
    platform: str
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None 