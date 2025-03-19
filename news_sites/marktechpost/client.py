from typing import Optional, List, Dict, Any
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from playwright.async_api import Page
import asyncio

logger = logging.getLogger(__name__)

class MarkTechPostClient:
    """MarkTechPost API客户端"""
    
    def __init__(self, config: dict):
        self.config = config
        self.base_url = config['base_url']
        self.latest_url = config['latest_url']
        self.max_articles = config['max_articles']
        
    async def get_latest_articles(self, page: Page, max_articles: int) -> List[str]:
        """获取最新文章链接"""
        
        logger.info(f"获取MarkTechPost最新文章链接，最大数量: {max_articles}")
        
        # 获取页面HTML内容
        html_content = await page.content()
        logger.info(f"获取到HTML内容，长度: {len(html_content)}")
        
        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 收集所有文章链接
        article_links = []
        
        # 打印当前页面的URL，帮助调试
        current_url = page.url
        logger.info(f"当前页面URL: {current_url}")
        
        # 输出一些页面基本信息帮助调试
        logger.info(f"页面标题: {await page.title()}")
        
        # 优化的选择器，特别针对MarkTechPost网站的常见文章链接选择器
        article_selectors = [
            'article.post h2.entry-title a', 
            '.archive-list .title a',
            '.entry-title a',
            '.search-results article a.title',
            '.post-title a',
            'h2.title a'
        ]
        
        # 尝试不同的选择器
        for selector in article_selectors:
            links = soup.select(selector)
            logger.info(f"使用选择器 '{selector}' 找到 {len(links)} 个链接")
            
            for link in links:
                if link.has_attr('href'):
                    url = link['href']
                    # 排除非文章链接
                    if '/category/' in url or '#' in url or 'page' in url or '/tag/' in url:
                        continue
                        
                    # 确保URL完整
                    if not url.startswith(('http://', 'https://')):
                        url = urljoin(self.base_url, url)
                    
                    # 确保链接为MarkTechPost域名且是文章链接格式（通常包含年份）
                    if ('marktechpost.com' in url and url not in article_links and 
                        (('/20' in url) or ('/article/' in url))):  # 大多数文章URL包含年份格式（如/2025/03/）
                        # 尝试获取标题
                        title = link.get_text(strip=True) if link.get_text(strip=True) else "未知标题"
                        logger.info(f"找到文章: {title} -> {url}")
                        article_links.append(url)
                        
                        if len(article_links) >= max_articles:
                            break
                            
            if len(article_links) >= max_articles:
                break
                
        # 如果没有找到足够的文章，尝试更加精确的方法查找文章链接
        if len(article_links) < max_articles:
            logger.info("通过常规选择器未找到足够文章，尝试更精确的方法")
            
            # 针对搜索结果页面的特殊处理
            if "?s=" in current_url:  # 判断是否是搜索结果页面
                # 查找所有可能的文章链接，主要关注那些包含年份的URL，这通常是文章链接的特征
                all_links = soup.find_all('a')
                for link in all_links:
                    if link.has_attr('href'):
                        url = link['href']
                        
                        # 确保URL完整
                        if not url.startswith(('http://', 'https://')):
                            url = urljoin(self.base_url, url)
                        
                        # 使用更严格的过滤条件：必须包含年份格式（通常文章URL都包含发布日期）
                        # 例如：https://www.marktechpost.com/2025/03/02/article-title/
                        if ('marktechpost.com' in url and 
                            url not in article_links and 
                            '/20' in url and  # 匹配年份格式
                            not any(exclude in url for exclude in ['/category/', '/tag/', '/page/', '/author/', 'wp-content', 'wp-admin', 'wp-login'])):
                            
                            # 尝试找到链接相关的标题（如果有）
                            title = "未知标题"
                            if link.get_text(strip=True):
                                title = link.get_text(strip=True)
                            elif link.has_attr('title'):
                                title = link['title']
                            
                            # 如果文本内容不为空且不太短（可能是导航链接），则添加这个链接
                            if len(title) > 15:  # 假设正常文章标题应该足够长
                                logger.info(f"通过更精确方法找到文章: {title} -> {url}")
                                article_links.append(url)
                                
                                if len(article_links) >= max_articles:
                                    break
        
        # 筛选出真正的文章链接，移除主页、账户页面等非文章链接
        filtered_links = []
        for url in article_links:
            # 排除常见的非文章URL模式
            if (self.base_url + '/' == url or  # 主页
                '/my-account' in url or        # 账户页面
                '/login' in url or             # 登录页面
                '/ai-magazine' in url or       # 杂志页面
                any(non_article in url for non_article in ['?signup', '/privacy-policy/', '/contact/', '/about/'])):
                logger.info(f"排除非文章链接: {url}")
                continue
            
            # 保留真正的文章链接
            filtered_links.append(url)
        
        # 将筛选后的链接作为结果
        article_links = filtered_links[:max_articles]
        
        logger.info(f"筛选后共找到{len(article_links)}个有效文章链接")
        for idx, url in enumerate(article_links):
            logger.info(f"有效文章{idx+1}: {url}")
        
        return article_links

    async def get_article_content(self, page: Page, url: str) -> Dict[str, Any]:
        """获取文章内容"""
        
        logger.info(f"获取文章内容: {url}")
        
        try:
            # 访问文章页面，并减少超时等待时间
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # 等待页面加载，但不等待所有网络请求完成
            await page.wait_for_load_state("domcontentloaded")
            
            # 获取页面HTML内容
            html_content = await page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 提取标题
            title_elem = soup.select_one('h1.entry-title, .td-post-title h1')
            title = title_elem.get_text(strip=True) if title_elem else "未知标题"
            logger.info(f"找到标题: {title}")
            
            # 提取作者
            author_elem = soup.select_one('.author a, .td-post-author-name a')
            author = author_elem.get_text(strip=True) if author_elem else "未知作者"
            # 移除"By"前缀，如果存在
            if author.startswith("By "):
                author = author[3:]
            logger.info(f"找到作者: {author}")
            
            # 提取发布日期
            date_elem = soup.select_one('time.entry-date, .td-post-date time')
            pub_date = ""
            if date_elem:
                if date_elem.has_attr('datetime'):
                    pub_date = date_elem['datetime']
                else:
                    pub_date = date_elem.get_text(strip=True)
            logger.info(f"找到发布日期: {pub_date}")
            
            # 提取文章内容 - 使用MarkTechPost网站的特定选择器
            content_elem = soup.select_one('.td-post-content.tagdiv-type')
            content = ""
            html_content_str = ""
            
            if content_elem:
                logger.info("找到文章内容元素")
                
                # 移除社交分享按钮
                for social_panel in content_elem.select('.swp_social_panel'):
                    social_panel.decompose()
                
                # 移除作者信息框
                for author_box in content_elem.select('.m-a-box, [class*="m-a-box"]'):
                    author_box.decompose()
                
                # 移除其他不需要的元素
                for unwanted in content_elem.select('.advertisement, .related-posts, .social-share, .widget, .sidebar, .comments, .code-block'):
                    unwanted.decompose()
                
                # 提取段落文本，在检测到作者信息部分时停止
                paragraphs = []
                for p in content_elem.select('p'):
                    # 检查是否是作者信息部分
                    parent_has_author_class = False
                    parent = p.parent
                    while parent:
                        if parent.get('class') and any('m-a-box' in cls for cls in parent.get('class')):
                            parent_has_author_class = True
                            break
                        parent = parent.parent
                    
                    # 如果不是作者信息部分的段落，则添加到内容中
                    if not parent_has_author_class:
                        paragraphs.append(p)
                        
                # 合并所有段落文本
                if paragraphs:
                    content = ' '.join([p.get_text(strip=True) for p in paragraphs])
                    # 保存HTML内容
                    html_content_str = ''.join(str(p) for p in paragraphs)
                    logger.info(f"提取到内容长度: {len(content)} 字符")
                else:
                    # 尝试直接获取内容，排除作者信息部分
                    # 先复制内容元素，以免修改原始元素
                    content_copy = content_elem
                    
                    # 移除作者信息部分
                    author_info = content_copy.find(class_=lambda c: c and 'm-a-box' in c)
                    if author_info:
                        # 获取作者信息之前的内容
                        content = ''.join(str(el) for el in author_info.previous_siblings if el.name)
                        html_content_str = content
                        content = BeautifulSoup(content, 'html.parser').get_text(strip=True)
                        logger.info(f"通过作者信息前的内容提取，长度: {len(content)} 字符")
                    else:
                        # 如果找不到作者信息，使用全部内容
                        content = content_elem.get_text(strip=True)
                        html_content_str = str(content_elem)
                        logger.info(f"未找到作者信息分隔，使用全部内容: {len(content)} 字符")
            else:
                logger.warning("未找到文章内容元素")
            
            # 如果内容为空，返回None
            if not content.strip():
                logger.warning(f"文章内容为空，将跳过保存: {url}")
                return None
                
            # 构建文章数据
            article_data = {
                'title': title,
                'author': author,
                'pub_date': pub_date,
                'content': content,
                'html_content': html_content_str,
                'url': url
            }
            
            return article_data
            
        except Exception as e:
            logger.error(f"获取文章内容失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None 