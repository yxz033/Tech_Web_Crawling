import asyncio
import logging
from typing import List, Dict, Any
from base.base_crawler import AbstractCrawler
from model.news_article import NewsArticle
from .client import MarkTechPostClient
from datetime import datetime
import warnings
import sys
import urllib.parse
from playwright.async_api import async_playwright, TimeoutError

# 添加警告过滤，抑制Windows平台上asyncio的管道关闭警告
if sys.platform.startswith('win'):
    warnings.filterwarnings("ignore", message="unclosed.*<_ProactorBasePipeTransport.*>", 
                           category=ResourceWarning)
    warnings.filterwarnings("ignore", message="unclosed.*<_OverlappedFuture.*>", 
                           category=ResourceWarning)
    warnings.filterwarnings("ignore", message="unclosed.*<asyncio.streams.StreamWriter.*>", 
                           category=ResourceWarning)

logger = logging.getLogger(__name__)

class MarkTechPostCrawler(AbstractCrawler):
    """MarkTechPost爬虫实现"""
    
    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.client = MarkTechPostClient(config)
        
    async def crawl(self) -> List[NewsArticle]:
        """爬取MarkTechPost最新文章"""
        try:
            logger.info("开始爬取MarkTechPost文章...")
            
            if not self.page:
                logger.error("浏览器未初始化")
                return []
            
            try:
                # 获取搜索关键词配置
                search_keywords = self.config.get('search_keywords', [])
                
                if search_keywords and len(search_keywords) > 0:
                    # 有搜索关键词，执行搜索爬取
                    logger.info(f"检测到搜索关键词: {search_keywords}，执行搜索爬取")
                    return await self._crawl_with_search(search_keywords)
                else:
                    # 无搜索关键词，执行常规爬取
                    logger.info("无搜索关键词，执行常规爬取")
                    return await self._crawl_regular()
                    
            except Exception as e:
                logger.error(f"爬取MarkTechPost文章时出错: {str(e)}")
                return []
            finally:
                # 等待一小段时间确保资源完全释放
                await asyncio.sleep(0.1)
            
        except Exception as e:
            logger.error(f"爬取MarkTechPost文章时出错: {str(e)}")
            return []
            
    async def _crawl_regular(self) -> List[NewsArticle]:
        """常规爬取方法"""
        # 访问最新文章页面
        latest_url = self.config.get('latest_url', 'https://www.marktechpost.com/category/tech-news/')
        logger.info(f"访问MarkTechPost最新文章页面: {latest_url}")
        
        # 设置用户代理
        await self.page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9'
        })
        
        # 访问页面
        await self.page.goto(latest_url, wait_until="networkidle")
        logger.info("页面加载完成")
        
        # 等待一段时间确保页面完全加载
        await asyncio.sleep(2)
            
        # 获取最新文章链接
        max_articles = self.config.get('max_articles', 10)
        article_links = await self.client.get_latest_articles(self.page, max_articles)
        logger.info(f"获取到{len(article_links)}篇文章链接")
        
        if not article_links:
            # 如果没有获取到链接，尝试直接从主页获取
            logger.warning("未从新闻页面获取到文章链接，尝试从主页获取")
            main_url = self.config.get('url', 'https://www.marktechpost.com')
            await self.page.goto(main_url, wait_until="networkidle")
            await asyncio.sleep(2)
            article_links = await self.client.get_latest_articles(self.page, max_articles)
            logger.info(f"从主页获取到{len(article_links)}篇文章链接")
        
        if not article_links:
            logger.warning("未获取到任何文章链接")
            return []
        
        # 爬取文章内容
        return await self._process_article_links(article_links)
            
    async def _crawl_with_search(self, keywords: List[str]) -> List[NewsArticle]:
        """根据关键词搜索并爬取"""
        all_articles = []
        max_articles_per_keyword = self.config.get('max_articles', 10)
        
        # 处理每个关键词
        for keyword in keywords:
            logger.info(f"使用关键词 '{keyword}' 进行搜索")
            
            try:
                # 直接使用URL搜索方式
                encoded_keyword = urllib.parse.quote(keyword)
                search_url = f"https://www.marktechpost.com/?s={encoded_keyword}"
                logger.info(f"访问搜索URL: {search_url}")
                
                # 访问搜索结果页面
                await self.page.goto(search_url, wait_until="networkidle")
                await asyncio.sleep(3)  # 等待页面完全加载
                
                # 输出页面标题和URL，用于调试
                page_title = await self.page.title()
                current_url = self.page.url
                logger.info(f"搜索页面标题: {page_title}")
                logger.info(f"搜索页面URL: {current_url}")
                
                # 检查页面是否有"Nothing Found"或类似无结果的信息
                page_content = await self.page.content()
                no_results_indicators = [
                    "Nothing Found", 
                    "没有找到", 
                    "No results found", 
                    "Sorry, no posts matched your criteria"
                ]
                
                no_results = False
                for indicator in no_results_indicators:
                    if indicator in page_content:
                        logger.warning(f"搜索 '{keyword}' 未找到任何结果 (检测到 '{indicator}')")
                        no_results = True
                        break
                
                if no_results:
                    logger.info(f"跳过关键词 '{keyword}' 并继续下一个关键词")
                    continue
                
                # 获取搜索结果中的文章链接
                logger.info(f"获取搜索结果中的文章链接(最多{max_articles_per_keyword}篇)")
                article_links = await self.client.get_latest_articles(self.page, max_articles_per_keyword)
                
                if not article_links:
                    logger.warning(f"搜索 '{keyword}' 未找到任何文章链接，可能没有结果或网页结构有变化")
                    continue
                    
                logger.info(f"搜索 '{keyword}' 获取到{len(article_links)}篇文章链接")
                
                # 处理文章内容，并设置关键词
                keyword_articles = await self._process_article_links(article_links, keyword)
                
                if keyword_articles:
                    all_articles.extend(keyword_articles)
                    logger.info(f"关键词 '{keyword}' 成功爬取{len(keyword_articles)}篇文章")
                else:
                    logger.warning(f"关键词 '{keyword}' 未成功获取任何文章内容")
                
            except Exception as e:
                logger.error(f"搜索关键词 '{keyword}' 时出错: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())  # 打印完整堆栈跟踪
                logger.info(f"继续处理下一个关键词...")
                
        # 输出总结信息
        if all_articles:
            logger.info(f"所有关键词搜索完成，共爬取到{len(all_articles)}篇文章")
            
            # 按关键词分组统计
            keyword_counts = {}
            for article in all_articles:
                if article.keyword:
                    keyword_counts[article.keyword] = keyword_counts.get(article.keyword, 0) + 1
            
            for kw, count in keyword_counts.items():
                logger.info(f"关键词 '{kw}' 爬取到 {count} 篇文章")
        else:
            logger.warning("所有关键词搜索完成，但未找到任何匹配的文章")
            
        return all_articles
        
    async def _process_article_links(self, article_links: List[str], keyword: str = None) -> List[NewsArticle]:
        """处理文章链接，爬取文章内容"""
        articles = []
        for url in article_links:
            try:
                # 使用同一个页面顺序处理每篇文章
                article_data = await self.client.get_article_content(self.page, url)
                
                # 检查article_data是否为None（表示内容为空或获取失败）
                if article_data is None:
                    logger.warning(f"未能获取有效内容或内容为空，跳过文章: {url}")
                    continue
                    
                # 转换为NewsArticle对象
                try:
                    # 处理日期字符串
                    pub_date = article_data.get('pub_date', '')
                    if isinstance(pub_date, str):
                        try:
                            # 尝试多种格式解析日期
                            try:
                                published_date = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                            except ValueError:
                                # 尝试其他可能的格式
                                date_formats = [
                                    '%Y-%m-%d %H:%M:%S',
                                    '%Y-%m-%d',
                                    '%b %d, %Y',
                                    '%B %d, %Y',
                                    '%d %b %Y',
                                    '%d %B %Y'
                                ]
                                for date_format in date_formats:
                                    try:
                                        published_date = datetime.strptime(pub_date, date_format)
                                        break
                                    except ValueError:
                                        continue
                                else:
                                    # 如果所有格式都失败，使用当前时间
                                    published_date = datetime.now()
                        except Exception as e:
                            logger.warning(f"日期解析失败: {pub_date}, 错误: {str(e)}")
                            published_date = datetime.now()
                    else:
                        published_date = datetime.now()
                    
                    article = NewsArticle(
                        title=article_data.get('title', '未知标题'),
                        author=article_data.get('author', '未知作者'),
                        published_date=published_date,
                        content=article_data.get('content', ''),
                        url=article_data.get('url', ''),
                        html_content=article_data.get('html_content', ''),
                        source='marktechpost',
                        keyword=keyword  # 设置关键词
                    )
                    articles.append(article)
                    logger.info(f"成功处理文章: {article_data.get('title')}")
                except Exception as e:
                    logger.error(f"创建文章对象失败: {str(e)}")
            except Exception as e:
                logger.error(f"爬取文章内容失败: {url}, 错误: {str(e)}")
        
        logger.info(f"成功爬取{len(articles)}篇文章")
        return articles

    async def parse(self, html_content: str) -> NewsArticle:
        """解析文章内容"""
        # 由于解析逻辑已经在client中实现,这里直接返回None
        return None 

    async def init_browser(self):
        """初始化浏览器"""
        if not self.browser:
            try:
                # 初始化playwright
                self.playwright = await async_playwright().start()
                
                # 初始化浏览器
                self.browser = await self.playwright.chromium.launch(headless=True)
                
                # 创建上下文和页面
                self.context = await self.browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080}
                )
                self.page = await self.context.new_page()
                
                # 设置默认超时时间为60秒，避免无限等待
                self.page.set_default_timeout(60000)
                
                # 配置页面资源过滤，阻止加载大量图片和媒体文件以提高速度
                await self.page.route('**/*.{png,jpg,jpeg,gif,svg,mp4,webm,mp3,ogg}', 
                                    lambda route: route.abort())
                
                # 配置页面拦截广告和跟踪脚本
                await self.page.route('**/{ads,analytics,tracking}/**', 
                                    lambda route: route.abort())
                                   
                logger.info("浏览器初始化完成")
                return True
            except Exception as e:
                logger.error(f"浏览器初始化失败: {str(e)}")
                return False
        return False 