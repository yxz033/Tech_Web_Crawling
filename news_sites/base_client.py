from abc import ABC, abstractmethod
from typing import List, Dict, Any
from playwright.async_api import Page

class BaseClient(ABC):
    """新闻网站客户端基类"""
    
    def __init__(self, config):
        """初始化基础客户端
        
        Args:
            config: 网站配置
        """
        self.base_url = config['url']
        self.latest_url = config['latest_url']
        self.max_articles = config['max_articles']
    
    @abstractmethod
    async def get_latest_articles(self, page: Page, max_articles: int) -> List[str]:
        """获取最新文章链接
        
        Args:
            page: Playwright页面对象
            max_articles: 最大文章数量
            
        Returns:
            文章URL列表
        """
        pass
    
    @abstractmethod
    async def get_article_content(self, page: Page, url: str) -> Dict[str, Any]:
        """获取文章内容
        
        Args:
            page: Playwright页面对象
            url: 文章URL
            
        Returns:
            文章内容字典
        """
        pass 