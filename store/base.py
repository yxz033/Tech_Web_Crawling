from abc import ABC, abstractmethod
from typing import List, Union
from model.news_article import NewsArticle
from model.platform_trends import TrendItem, TwitterTrend, GithubTrend, HuggingfaceTrend

class BaseStore(ABC):
    """存储基类"""
    
    @abstractmethod
    async def save_article(self, article: NewsArticle) -> bool:
        """保存文章"""
        pass
        
    @abstractmethod
    async def save_articles(self, articles: List[NewsArticle]) -> bool:
        """批量保存文章"""
        pass
        
    @abstractmethod
    async def save_trend(self, trend: Union[TwitterTrend, GithubTrend, HuggingfaceTrend]) -> bool:
        """保存趋势项"""
        pass
        
    @abstractmethod
    async def save_trends(self, trends: List[Union[TwitterTrend, GithubTrend, HuggingfaceTrend]], platform: str) -> bool:
        """批量保存趋势项"""
        pass
        
    @abstractmethod
    async def get_article_by_url(self, url: str) -> Union[NewsArticle, None]:
        """根据URL获取文章"""
        pass
        
    @abstractmethod
    async def get_trend_by_url(self, url: str, platform: str) -> Union[TrendItem, None]:
        """根据URL获取趋势项"""
        pass 