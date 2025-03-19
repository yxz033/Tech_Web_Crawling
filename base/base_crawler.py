from abc import ABC, abstractmethod
from typing import List, Optional
import asyncio
from playwright.async_api import async_playwright, Browser, Page

class AbstractCrawler(ABC):
    """爬虫抽象基类"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
    async def init_browser(self):
        """初始化浏览器"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        self.page = await self.browser.new_page()
        
    async def close_browser(self):
        """关闭浏览器"""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
            
    @abstractmethod
    async def crawl(self):
        """爬取数据的主方法"""
        pass
    
    @abstractmethod
    async def parse(self, html_content: str):
        """解析HTML内容"""
        pass
    
    async def save(self, data):
        """保存数据"""
        pass 