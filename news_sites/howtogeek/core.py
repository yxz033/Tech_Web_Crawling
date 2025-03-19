import asyncio
import logging
from typing import List, Dict, Any
from base.base_crawler import AbstractCrawler
from model.news_article import NewsArticle
from .client import HowToGeekClient
from datetime import datetime
import warnings
import sys
import urllib.parse

# 添加警告过滤，抑制Windows平台上asyncio的管道关闭警告
if sys.platform.startswith('win'):
    # 过滤asyncio的ResourceWarning
    warnings.filterwarnings("ignore", message="unclosed.*<_ProactorBasePipeTransport.*>", 
                           category=ResourceWarning)
    warnings.filterwarnings("ignore", message="unclosed.*<_OverlappedFuture.*>", 
                           category=ResourceWarning)
    warnings.filterwarnings("ignore", message="unclosed.*<asyncio.streams.StreamWriter.*>", 
                           category=ResourceWarning)

logger = logging.getLogger(__name__)

class HowToGeekCrawler(AbstractCrawler):
    """HowToGeek爬虫实现"""
    
    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.client = HowToGeekClient(config)
        
    async def crawl(self) -> List[NewsArticle]:
        """爬取HowToGeek最新文章"""
        try:
            logger.info("开始爬取HowToGeek文章...")
            
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
                logger.error(f"爬取HowToGeek文章时出错: {str(e)}")
                return []
            finally:
                # 等待一小段时间确保资源完全释放
                await asyncio.sleep(0.1)
            
        except Exception as e:
            logger.error(f"爬取HowToGeek文章时出错: {str(e)}")
            return []
            
    async def _crawl_regular(self) -> List[NewsArticle]:
        """常规爬取方法"""
        # 首先访问最新文章页面
        latest_url = self.config.get('latest_url', 'https://www.howtogeek.com/news/')
        logger.info(f"访问HowToGeek最新文章页面: {latest_url}")
        
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
            main_url = self.config.get('url', 'https://www.howtogeek.com')
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
                # 1. 直接使用URL搜索方式（作为首选方法）
                # 对关键词进行URL编码，确保中文和特殊字符能正确处理
                encoded_keyword = urllib.parse.quote(keyword)
                search_url = f"https://www.howtogeek.com/search/?q={encoded_keyword}"
                logger.info(f"使用直接URL搜索方式: {search_url}")
                
                # 访问搜索结果页面
                await self.page.goto(search_url, wait_until="networkidle")
                await asyncio.sleep(5)  # 等待页面完全加载
                
                # 输出页面标题和URL，用于调试
                page_title = await self.page.title()
                current_url = self.page.url
                logger.info(f"搜索页面标题: {page_title}")
                logger.info(f"搜索页面URL: {current_url}")
                
                # 获取搜索结果中的文章链接
                logger.info(f"获取搜索结果中的文章链接(最多{max_articles_per_keyword}篇)")
                article_links = await self.client.get_latest_articles(self.page, max_articles_per_keyword)
                logger.info(f"搜索 '{keyword}' 获取到{len(article_links)}篇文章链接")
                
                # 如果找不到任何文章，尝试备用方法
                if not article_links:
                    logger.warning(f"直接URL搜索未找到任何文章，尝试备用搜索方法")
                    article_links = await self._fallback_search(keyword, max_articles_per_keyword)
                    
                if article_links:
                    # 处理文章内容，并设置关键词
                    keyword_articles = await self._process_article_links(article_links, keyword)
                    all_articles.extend(keyword_articles)
                    logger.info(f"关键词 '{keyword}' 成功爬取{len(keyword_articles)}篇文章")
                else:
                    logger.warning(f"关键词 '{keyword}' 未找到任何文章")
                
            except Exception as e:
                logger.error(f"搜索关键词 '{keyword}' 时出错: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())  # 打印完整堆栈跟踪
                
                # 尝试备用方法
                try:
                    logger.info(f"尝试使用备用方法搜索关键词 '{keyword}'")
                    article_links = await self._fallback_search(keyword, max_articles_per_keyword)
                    
                    if article_links:
                        # 处理文章内容，并设置关键词
                        keyword_articles = await self._process_article_links(article_links, keyword)
                        all_articles.extend(keyword_articles)
                        logger.info(f"使用备用方法成功爬取 '{keyword}' 的{len(keyword_articles)}篇文章")
                except Exception as e2:
                    logger.error(f"备用搜索方法也失败: {str(e2)}")
                
        # 返回所有爬取的文章
        logger.info(f"所有关键词搜索完成，共爬取到{len(all_articles)}篇文章")
        return all_articles

    async def _fallback_search(self, keyword: str, max_articles: int) -> List[str]:
        """备用搜索方法，通过点击UI元素执行搜索"""
        logger.info(f"执行备用搜索方法，关键词: '{keyword}'")
        
        # 访问主页
        main_url = self.config.get('url', 'https://www.howtogeek.com')
        logger.info(f"访问主页: {main_url}")
        await self.page.goto(main_url, wait_until="networkidle")
        await asyncio.sleep(5)  # 增加等待时间，确保页面完全加载
        
        try:
            # 1. 点击侧边栏菜单按钮
            logger.info("尝试点击侧边栏菜单按钮")
            sidebar_selector = "label.menu-icon.topnav-icon.icon.i-menu-new.css-menu--toggle"
            try:
                await self.page.wait_for_selector(sidebar_selector, timeout=10000)
                await self.page.click(sidebar_selector)
                logger.info("成功点击侧边栏菜单按钮")
                await asyncio.sleep(2)  # 等待侧边栏展开
            except Exception as e:
                logger.warning(f"点击侧边栏按钮失败: {str(e)}")
                # 如果找不到精确选择器，尝试更宽松的选择器
                try:
                    await self.page.click("label.menu-icon")
                    logger.info("成功使用备选选择器点击侧边栏按钮")
                    await asyncio.sleep(2)
                except Exception as e2:
                    logger.error(f"点击侧边栏按钮(备选方法)失败: {str(e2)}")
            
            # 2. 点击搜索按钮
            logger.info("尝试点击搜索按钮")
            search_button_selector = "span.menu-icon.topbar-icon.icon.i-search-menu"
            try:
                await self.page.wait_for_selector(search_button_selector, timeout=10000)
                await self.page.click(search_button_selector)
                logger.info("成功点击搜索按钮")
                await asyncio.sleep(2)  # 等待搜索框出现
            except Exception as e:
                logger.warning(f"点击搜索按钮失败: {str(e)}")
                # 尝试备选选择器或JavaScript方法
                try:
                    await self.page.click("span.icon.i-search-menu")
                    logger.info("成功使用备选选择器点击搜索按钮")
                    await asyncio.sleep(2)
                except Exception as e2:
                    logger.error(f"点击搜索按钮(备选方法)失败: {str(e2)}")
                    
                    # 使用JavaScript执行点击
                    try:
                        logger.info("尝试使用JavaScript点击搜索按钮")
                        await self.page.evaluate("""
                            () => {
                                // 尝试查找所有可能的搜索按钮
                                const searchButtons = [
                                    ...document.querySelectorAll('span.icon.i-search-menu'),
                                    ...document.querySelectorAll('[class*="search"]'),
                                    ...document.querySelectorAll('a[href*="search"]'),
                                    ...document.querySelectorAll('button[aria-label*="search" i]')
                                ];
                                
                                // 点击找到的第一个搜索按钮
                                for (const btn of searchButtons) {
                                    if (btn.offsetParent !== null) {  // 检查元素是否可见
                                        btn.click();
                                        console.log('Clicked search button via JS:', btn);
                                        return true;
                                    }
                                }
                                return false;
                            }
                        """)
                        logger.info("通过JavaScript点击搜索按钮")
                        await asyncio.sleep(2)
                    except Exception as e3:
                        logger.error(f"使用JavaScript点击搜索按钮失败: {str(e3)}")
                        return []  # 如果所有方法都失败，返回空列表
            
            # 3. 等待搜索框出现
            logger.info("等待搜索框出现")
            search_input_selector = '#js-search-input'
            try:
                await self.page.wait_for_selector(search_input_selector, timeout=10000)
                logger.info("成功找到搜索输入框")
            except Exception as e:
                logger.warning(f"等待搜索框出现失败: {str(e)}")
                
                # 尝试更通用的选择器
                search_input_selector = "input[type='text'][name='q'], input[type='search'], input[placeholder*='search' i]"
                try:
                    await self.page.wait_for_selector(search_input_selector, timeout=10000)
                    logger.info(f"使用通用选择器找到搜索框: {search_input_selector}")
                except Exception as e2:
                    logger.error(f"使用通用选择器查找搜索框失败: {str(e2)}")
                    return []  # 如果找不到搜索框，返回空列表
            
            # 4. 输入关键词并搜索
            try:
                # 清空搜索框并输入关键词
                logger.info(f"清空搜索框并输入关键词: {keyword}")
                await self.page.fill(search_input_selector, '')
                await asyncio.sleep(1)
                await self.page.fill(search_input_selector, keyword)
                await asyncio.sleep(2)  # 等待自动建议显示
                
                # 按回车键执行搜索
                logger.info("按回车键执行搜索")
                await self.page.press(search_input_selector, 'Enter')
                
                # 等待搜索结果加载
                logger.info("等待搜索结果加载")
                await self.page.wait_for_load_state("networkidle", timeout=30000)
                await asyncio.sleep(5)  # 等待加载完成
                
                # 获取搜索结果中的文章链接
                logger.info(f"获取搜索结果中的文章链接(最多{max_articles}篇)")
                article_links = await self.client.get_latest_articles(self.page, max_articles)
                logger.info(f"搜索 '{keyword}' 获取到{len(article_links)}篇文章链接")
                
                return article_links
                
            except Exception as e:
                logger.error(f"输入关键词并搜索失败: {str(e)}")
                return []
                
        except Exception as e:
            logger.error(f"备用搜索方法失败: {str(e)}")
            return []
        
    async def _process_article_links(self, article_links: List[str], keyword: str = None) -> List[NewsArticle]:
        """处理文章链接，爬取文章内容"""
        articles = []
        for url in article_links:
            try:
                # 使用同一个页面顺序处理每篇文章
                article_data = await self.client.get_article_content(self.page, url)
                if article_data:
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
                            html_content=article_data.get('content', ''),
                            source='howtogeek',
                            keyword=keyword  # 设置关键词
                        )
                        articles.append(article)
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