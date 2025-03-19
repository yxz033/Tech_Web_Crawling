from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from .trend_item import TrendItem

@dataclass
class TwitterTrend(TrendItem):
    """Twitter趋势模型"""
    tweet_count: str = ""
    
    def __post_init__(self):
        self.platform = 'twitter'

@dataclass
class GithubTrend(TrendItem):
    """GitHub趋势模型"""
    language: str = "Unknown"
    stars: int = 0
    
    def __post_init__(self):
        self.platform = 'github'

@dataclass
class HuggingfaceTrend(TrendItem):
    """Huggingface趋势模型"""
    downloads: str = "0"
    tags: List[str] = None
    
    def __post_init__(self):
        self.platform = 'huggingface'
        if self.tags is None:
            self.tags = [] 