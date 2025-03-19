import mysql.connector
from mysql.connector import Error
from typing import List, Union, Optional
import logging
from datetime import datetime
from .base import BaseStore
from model.news_article import NewsArticle
from model.platform_trends import TrendItem, TwitterTrend, GithubTrend, HuggingfaceTrend

logger = logging.getLogger(__name__)

class MySQLStore(BaseStore):
    """MySQL存储实现"""
    
    def __init__(self, config: dict):
        self.config = config
        self.connection = None
        self.connect()
        self.init_tables()
        
    def connect(self):
        """连接数据库"""
        try:
            self.connection = mysql.connector.connect(
                host=self.config['host'],
                port=self.config['port'],
                user=self.config['user'],
                password=self.config['password'],
                database=self.config['database']
            )
            logger.info("成功连接到MySQL数据库")
        except Error as e:
            logger.error(f"连接MySQL数据库失败: {str(e)}")
            raise
            
    def init_tables(self):
        """初始化数据表"""
        try:
            cursor = self.connection.cursor()
            
            # 创建文章表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    author VARCHAR(100) NOT NULL,
                    published_date DATETIME NOT NULL,
                    content TEXT NOT NULL,
                    html_content TEXT NOT NULL,
                    url VARCHAR(255) NOT NULL UNIQUE,
                    source VARCHAR(50) NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            
            # 创建趋势表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trends (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    rank INT NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    description TEXT NOT NULL,
                    url VARCHAR(255) NOT NULL UNIQUE,
                    platform VARCHAR(50) NOT NULL,
                    tweet_count VARCHAR(50),
                    language VARCHAR(50),
                    stars INT,
                    downloads VARCHAR(50),
                    tags JSON,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            
            self.connection.commit()
            logger.info("成功初始化数据表")
            
        except Error as e:
            logger.error(f"初始化数据表失败: {str(e)}")
            raise
        finally:
            cursor.close()
            
    async def save_article(self, article: NewsArticle) -> bool:
        """保存文章"""
        try:
            cursor = self.connection.cursor()
            
            # 检查文章是否已存在
            cursor.execute("SELECT id FROM articles WHERE url = %s", (article.url,))
            if cursor.fetchone():
                return True
                
            # 插入新文章
            cursor.execute("""
                INSERT INTO articles (title, author, published_date, content, html_content, url, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                article.title,
                article.author,
                article.published_date,
                article.content,
                article.html_content,
                article.url,
                article.source
            ))
            
            self.connection.commit()
            return True
            
        except Error as e:
            logger.error(f"保存文章失败: {str(e)}")
            return False
        finally:
            cursor.close()
            
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
            cursor = self.connection.cursor()
            
            # 检查趋势项是否已存在
            cursor.execute("SELECT id FROM trends WHERE url = %s AND platform = %s", (trend.url, trend.platform))
            if cursor.fetchone():
                return True
                
            # 准备趋势项数据
            trend_data = {
                'rank': trend.rank,
                'name': trend.name,
                'description': trend.description,
                'url': trend.url,
                'platform': trend.platform
            }
            
            # 根据趋势类型添加特定字段
            if isinstance(trend, TwitterTrend):
                trend_data['tweet_count'] = trend.tweet_count
            elif isinstance(trend, GithubTrend):
                trend_data['language'] = trend.language
                trend_data['stars'] = trend.stars
            elif isinstance(trend, HuggingfaceTrend):
                trend_data['downloads'] = trend.downloads
                trend_data['tags'] = trend.tags
                
            # 构建SQL语句
            fields = ', '.join(trend_data.keys())
            placeholders = ', '.join(['%s'] * len(trend_data))
            sql = f"INSERT INTO trends ({fields}) VALUES ({placeholders})"
            
            # 执行插入
            cursor.execute(sql, list(trend_data.values()))
            
            self.connection.commit()
            return True
            
        except Error as e:
            logger.error(f"保存趋势项失败: {str(e)}")
            return False
        finally:
            cursor.close()
            
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
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM articles WHERE url = %s", (url,))
            row = cursor.fetchone()
            
            if row:
                return NewsArticle(
                    title=row['title'],
                    author=row['author'],
                    published_date=row['published_date'],
                    content=row['content'],
                    html_content=row['html_content'],
                    url=row['url'],
                    source=row['source'],
                    id=row['id'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
            return None
            
        except Error as e:
            logger.error(f"获取文章失败: {str(e)}")
            return None
        finally:
            cursor.close()
            
    async def get_trend_by_url(self, url: str, platform: str) -> Optional[TrendItem]:
        """根据URL获取趋势项"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM trends WHERE url = %s AND platform = %s", (url, platform))
            row = cursor.fetchone()
            
            if not row:
                return None
                
            # 根据平台类型创建对应的趋势对象
            if platform == 'twitter':
                return TwitterTrend(
                    rank=row['rank'],
                    name=row['name'],
                    description=row['description'],
                    url=row['url'],
                    tweet_count=row['tweet_count']
                )
            elif platform == 'github':
                return GithubTrend(
                    rank=row['rank'],
                    name=row['name'],
                    description=row['description'],
                    url=row['url'],
                    language=row['language'],
                    stars=row['stars']
                )
            elif platform == 'huggingface':
                return HuggingfaceTrend(
                    rank=row['rank'],
                    name=row['name'],
                    description=row['description'],
                    url=row['url'],
                    downloads=row['downloads'],
                    tags=row['tags']
                )
            return None
            
        except Error as e:
            logger.error(f"获取趋势项失败: {str(e)}")
            return None
        finally:
            cursor.close()
            
    def close(self):
        """关闭数据库连接"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("已关闭MySQL数据库连接") 