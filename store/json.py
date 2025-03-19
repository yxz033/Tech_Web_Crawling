import json
from typing import List, Union, Optional
import logging
from datetime import datetime
import os
from .base import BaseStore
from model.news_article import NewsArticle
from model.platform_trends import TrendItem, TwitterTrend, GithubTrend, HuggingfaceTrend

logger = logging.getLogger(__name__)

class JSONStore(BaseStore):
    """JSON存储实现"""
    
    def __init__(self, config: dict):
        self.config = config
        self.articles_file = config['json_path']
        self.trends_file = 'data/trends.json'
        self.init_files()
        
    def init_files(self):
        """初始化JSON文件"""
        try:
            # 创建data目录
            os.makedirs(os.path.dirname(self.articles_file), exist_ok=True)
            os.makedirs(os.path.dirname(self.trends_file), exist_ok=True)
            
            # 创建文章JSON文件
            if not os.path.exists(self.articles_file):
                with open(self.articles_file, 'w', encoding='utf-8') as f:
                    json.dump([], f, ensure_ascii=False, indent=2)
                    
            # 创建趋势JSON文件
            if not os.path.exists(self.trends_file):
                with open(self.trends_file, 'w', encoding='utf-8') as f:
                    json.dump([], f, ensure_ascii=False, indent=2)
                    
            logger.info("成功初始化JSON文件")
            
        except Exception as e:
            logger.error(f"初始化JSON文件失败: {str(e)}")
            raise
            
    def _load_json(self, file_path: str) -> list:
        """加载JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载JSON文件失败: {str(e)}")
            return []
            
    def _save_json(self, file_path: str, data: list):
        """保存JSON文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存JSON文件失败: {str(e)}")
            raise
            
    async def save_article(self, article: NewsArticle) -> bool:
        """保存文章"""
        try:
            # 加载现有文章
            articles = self._load_json(self.articles_file)
            
            # 检查文章是否已存在
            for index, existing_article in enumerate(articles):
                if existing_article['url'] == article.url:
                    logger.info(f"找到已存在文章: {article.title}")
                    
                    # 检查内容是否有变化
                    content_changed = (
                        existing_article['content'] != article.content or
                        existing_article['html_content'] != article.html_content or
                        existing_article['title'] != article.title or
                        existing_article['author'] != article.author
                    )
                    
                    if content_changed:
                        # 更新现有文章
                        logger.info(f"更新文章内容: {article.title}")
                        existing_article['title'] = article.title
                        existing_article['author'] = article.author
                        existing_article['published_date'] = article.published_date.isoformat()
                        existing_article['content'] = article.content
                        existing_article['html_content'] = article.html_content
                        existing_article['updated_at'] = datetime.now().isoformat()
                        
                        # 如果关键词存在且不同，则更新关键词
                        if article.keyword and existing_article.get('keyword') != article.keyword:
                            existing_article['keyword'] = article.keyword
                            logger.info(f"更新文章关键词为: {article.keyword}")
                        
                        # 保存更新后的文章
                        self._save_json(self.articles_file, articles)
                    else:
                        logger.info(f"文章内容无变化，跳过更新: {article.title}")
                        
                    return True
                    
            # 如果文章不存在，则添加新文章
            logger.info(f"添加新文章: {article.title}")
            article_data = {
                'id': len(articles) + 1,
                'title': article.title,
                'author': article.author,
                'published_date': article.published_date.isoformat(),
                'content': article.content,
                'html_content': article.html_content,
                'url': article.url,
                'source': article.source,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'keyword': article.keyword
            }
            
            # 添加新文章
            articles.append(article_data)
            
            # 保存到文件
            self._save_json(self.articles_file, articles)
            
            return True
            
        except Exception as e:
            logger.error(f"保存文章失败: {str(e)}")
            return False
            
    async def save_articles(self, articles: List[NewsArticle]) -> bool:
        """批量保存文章"""
        try:
            success_count = 0
            for article in articles:
                if await self.save_article(article):
                    success_count += 1
            
            logger.info(f"批量保存文章完成: {success_count}/{len(articles)} 篇保存成功")
            return success_count == len(articles)
        except Exception as e:
            logger.error(f"批量保存文章失败: {str(e)}")
            return False
            
    async def save_trend(self, trend: Union[TwitterTrend, GithubTrend, HuggingfaceTrend]) -> bool:
        """保存趋势项"""
        try:
            # 加载现有趋势
            trends = self._load_json(self.trends_file)
            
            # 检查趋势项是否已存在
            if any(t['url'] == trend.url and t['platform'] == trend.platform for t in trends):
                return True
                
            # 准备趋势项数据
            trend_data = {
                'id': len(trends) + 1,
                'rank': trend.rank,
                'name': trend.name,
                'description': trend.description,
                'url': trend.url,
                'platform': trend.platform,
                'tweet_count': '',
                'language': '',
                'stars': '',
                'downloads': '',
                'tags': [],
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
                trend_data['tags'] = trend.tags
                
            # 添加新趋势
            trends.append(trend_data)
            
            # 保存到文件
            self._save_json(self.trends_file, trends)
            
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
            articles = self._load_json(self.articles_file)
            for article in articles:
                if article['url'] == url:
                    return NewsArticle(
                        title=article['title'],
                        author=article['author'],
                        published_date=datetime.fromisoformat(article['published_date']),
                        content=article['content'],
                        html_content=article['html_content'],
                        url=article['url'],
                        source=article['source'],
                        id=article['id'],
                        created_at=datetime.fromisoformat(article['created_at']),
                        updated_at=datetime.fromisoformat(article['updated_at']),
                        keyword=article.get('keyword')
                    )
            return None
            
        except Exception as e:
            logger.error(f"获取文章失败: {str(e)}")
            return None
            
    async def get_trend_by_url(self, url: str, platform: str) -> Optional[TrendItem]:
        """根据URL获取趋势项"""
        try:
            trends = self._load_json(self.trends_file)
            for trend in trends:
                if trend['url'] == url and trend['platform'] == platform:
                    # 根据平台类型创建对应的趋势对象
                    if platform == 'twitter':
                        return TwitterTrend(
                            rank=trend['rank'],
                            name=trend['name'],
                            description=trend['description'],
                            url=trend['url'],
                            tweet_count=trend['tweet_count']
                        )
                    elif platform == 'github':
                        return GithubTrend(
                            rank=trend['rank'],
                            name=trend['name'],
                            description=trend['description'],
                            url=trend['url'],
                            language=trend['language'],
                            stars=trend['stars']
                        )
                    elif platform == 'huggingface':
                        return HuggingfaceTrend(
                            rank=trend['rank'],
                            name=trend['name'],
                            description=trend['description'],
                            url=trend['url'],
                            downloads=trend['downloads'],
                            tags=trend['tags']
                        )
            return None
            
        except Exception as e:
            logger.error(f"获取趋势项失败: {str(e)}")
            return None 