import csv
import json
from typing import List, Union, Optional
import logging
from datetime import datetime
import os
from .base import BaseStore
from model.news_article import NewsArticle
from model.platform_trends import TrendItem, TwitterTrend, GithubTrend, HuggingfaceTrend

logger = logging.getLogger(__name__)

class CSVStore(BaseStore):
    """CSV存储实现"""
    
    def __init__(self, config: dict):
        self.config = config
        self.articles_file = config['csv_path']
        self.trends_file = 'data/trends.csv'
        self.init_files()
        
    def init_files(self):
        """初始化CSV文件"""
        try:
            # 创建data目录
            os.makedirs(os.path.dirname(self.articles_file), exist_ok=True)
            os.makedirs(os.path.dirname(self.trends_file), exist_ok=True)
            
            # 创建文章CSV文件
            if not os.path.exists(self.articles_file):
                with open(self.articles_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        'id', 'title', 'author', 'published_date', 'content',
                        'html_content', 'url', 'source', 'created_at', 'updated_at'
                    ])
                    
            # 创建趋势CSV文件
            if not os.path.exists(self.trends_file):
                with open(self.trends_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        'id', 'rank', 'name', 'description', 'url', 'platform',
                        'tweet_count', 'language', 'stars', 'downloads', 'tags',
                        'created_at', 'updated_at'
                    ])
                    
            logger.info("成功初始化CSV文件")
            
        except Exception as e:
            logger.error(f"初始化CSV文件失败: {str(e)}")
            raise
            
    async def save_article(self, article: NewsArticle) -> bool:
        """保存文章"""
        try:
            # 检查文章是否已存在
            if await self.get_article_by_url(article.url):
                return True
                
            # 获取当前最大ID
            max_id = 0
            with open(self.articles_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    max_id = max(max_id, int(row['id'] or 0))
                    
            # 准备文章数据
            article_data = {
                'id': max_id + 1,
                'title': article.title,
                'author': article.author,
                'published_date': article.published_date.isoformat(),
                'content': article.content,
                'html_content': article.html_content,
                'url': article.url,
                'source': article.source,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # 写入CSV
            with open(self.articles_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=article_data.keys())
                writer.writerow(article_data)
                
            return True
            
        except Exception as e:
            logger.error(f"保存文章失败: {str(e)}")
            return False
            
    async def save_articles(self, articles: List[NewsArticle]) -> bool:
        """批量保存文章"""
        try:
            for article in articles:
                await self.save_article(article)
            return True
        except Exception as e:
            logger.error(f"批量保存文章失败: {str(e)}")
            return False
            
    async def save_trend(self, trend: Union[TwitterTrend, GithubTrend, HuggingfaceTrend]) -> bool:
        """保存趋势项"""
        try:
            # 检查趋势项是否已存在
            if await self.get_trend_by_url(trend.url, trend.platform):
                return True
                
            # 获取当前最大ID
            max_id = 0
            with open(self.trends_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    max_id = max(max_id, int(row['id'] or 0))
                    
            # 准备趋势项数据
            trend_data = {
                'id': max_id + 1,
                'rank': trend.rank,
                'name': trend.name,
                'description': trend.description,
                'url': trend.url,
                'platform': trend.platform,
                'tweet_count': '',
                'language': '',
                'stars': '',
                'downloads': '',
                'tags': '',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # 根据趋势类型设置特定字段
            if isinstance(trend, TwitterTrend):
                trend_data['tweet_count'] = trend.tweet_count
            elif isinstance(trend, GithubTrend):
                trend_data['language'] = trend.language
                trend_data['stars'] = trend.stars
            elif isinstance(trend, HuggingfaceTrend):
                trend_data['downloads'] = trend.downloads
                trend_data['tags'] = json.dumps(trend.tags)
                
            # 写入CSV
            with open(self.trends_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=trend_data.keys())
                writer.writerow(trend_data)
                
            return True
            
        except Exception as e:
            logger.error(f"保存趋势项失败: {str(e)}")
            return False
            
    async def save_trends(self, trends: List[Union[TwitterTrend, GithubTrend, HuggingfaceTrend]], platform: str) -> bool:
        """批量保存趋势项"""
        try:
            for trend in trends:
                await self.save_trend(trend)
            return True
        except Exception as e:
            logger.error(f"批量保存趋势项失败: {str(e)}")
            return False
            
    async def get_article_by_url(self, url: str) -> Optional[NewsArticle]:
        """根据URL获取文章"""
        try:
            with open(self.articles_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['url'] == url:
                        return NewsArticle(
                            title=row['title'],
                            author=row['author'],
                            published_date=datetime.fromisoformat(row['published_date']),
                            content=row['content'],
                            html_content=row['html_content'],
                            url=row['url'],
                            source=row['source'],
                            id=int(row['id']),
                            created_at=datetime.fromisoformat(row['created_at']),
                            updated_at=datetime.fromisoformat(row['updated_at'])
                        )
            return None
            
        except Exception as e:
            logger.error(f"获取文章失败: {str(e)}")
            return None
            
    async def get_trend_by_url(self, url: str, platform: str) -> Optional[TrendItem]:
        """根据URL获取趋势项"""
        try:
            with open(self.trends_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['url'] == url and row['platform'] == platform:
                        # 根据平台类型创建对应的趋势对象
                        if platform == 'twitter':
                            return TwitterTrend(
                                rank=int(row['rank']),
                                name=row['name'],
                                description=row['description'],
                                url=row['url'],
                                tweet_count=row['tweet_count']
                            )
                        elif platform == 'github':
                            return GithubTrend(
                                rank=int(row['rank']),
                                name=row['name'],
                                description=row['description'],
                                url=row['url'],
                                language=row['language'],
                                stars=int(row['stars']) if row['stars'] else 0
                            )
                        elif platform == 'huggingface':
                            return HuggingfaceTrend(
                                rank=int(row['rank']),
                                name=row['name'],
                                description=row['description'],
                                url=row['url'],
                                downloads=row['downloads'],
                                tags=json.loads(row['tags']) if row['tags'] else []
                            )
            return None
            
        except Exception as e:
            logger.error(f"获取趋势项失败: {str(e)}")
            return None 