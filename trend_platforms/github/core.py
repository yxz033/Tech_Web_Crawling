import logging
from typing import List
from base.base_crawler import AbstractCrawler
from model.platform_trends import GithubTrend
from .client import GithubClient

logger = logging.getLogger(__name__)

class GithubCrawler(AbstractCrawler):
    """GitHub趋势爬虫实现"""
    
    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.client = GithubClient(config)
        
    async def crawl(self) -> List[GithubTrend]:
        """爬取GitHub趋势仓库"""
        try:
            logger.info("开始爬取GitHub趋势仓库...")
            
            # 获取趋势仓库列表
            repos = await self.client.get_trending_repos()
            
            logger.info(f"成功爬取{len(repos)}个趋势仓库")
            return repos
            
        except Exception as e:
            logger.error(f"爬取GitHub趋势仓库时出错: {str(e)}")
            return []
            
    async def parse(self, html_content: str) -> GithubTrend:
        """解析仓库内容"""
        # 由于解析逻辑已经在client中实现,这里直接返回None
        return None 