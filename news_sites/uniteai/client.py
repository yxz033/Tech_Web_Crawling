from typing import Optional, List, Dict, Any
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from playwright.async_api import Page
import asyncio

logger = logging.getLogger(__name__)

class UniteAIClient:
    """UniteAI API客户端"""
    
    def __init__(self, config: dict):
        self.config = config
        self.base_url = config['url']
        self.latest_url = config['latest_url']
        self.max_articles = config['max_articles']
        
    async def get_latest_articles(self, page: Page, max_articles: int) -> List[str]:
        """获取最新文章链接"""
        
        logger.info(f"获取UniteAI最新文章链接，最大数量: {max_articles}")
        
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
        
        # 1. 查找第一种文章区域: mvp-widget-feat1-wrap中的文章链接
        logger.info("查找第一种文章区域中的链接")
        feat1_links = soup.select('.mvp-widget-feat1-wrap a[href*="unite.ai"]')
        for link in feat1_links:
            if link.has_attr('href'):
                url = link['href']
                # 确保URL完整
                if not url.startswith(('http://', 'https://')):
                    url = urljoin(self.base_url, url)
                
                # 获取文章标题(如果存在)
                title_elem = link.select_one('h2')
                title = title_elem.get_text(strip=True) if title_elem else "未知标题"
                
                logger.info(f"找到文章(区域1): {title} -> {url}")
                
                if url not in article_links:
                    article_links.append(url)
                    
                    if len(article_links) >= max_articles:
                        break
        
        # 2. 查找第二种文章区域: mvp-widget-feat1-cont中的文章链接
        if len(article_links) < max_articles:
            logger.info("查找第二种文章区域中的链接")
            feat1_cont_links = soup.select('.mvp-widget-feat1-cont a[href*="unite.ai"]')
            for link in feat1_cont_links:
                if link.has_attr('href'):
                    url = link['href']
                    # 确保URL完整
                    if not url.startswith(('http://', 'https://')):
                        url = urljoin(self.base_url, url)
                    
                    # 避免重复链接
                    if url not in article_links:
                        # 获取文章标题(如果存在)
                        title_elem = link.select_one('h2')
                        title = title_elem.get_text(strip=True) if title_elem else "未知标题"
                        
                        logger.info(f"找到文章(区域2): {title} -> {url}")
                        article_links.append(url)
                        
                        if len(article_links) >= max_articles:
                            break
        
        # 3. 查找第三种文章区域: mvp-blog-story-list中的文章
        if len(article_links) < max_articles:
            logger.info("查找第三种文章区域中的链接")
            blog_links = soup.select('.mvp-blog-story-list a[href*="unite.ai"]')
            for link in blog_links:
                if link.has_attr('href'):
                    url = link['href']
                    # 确保URL完整
                    if not url.startswith(('http://', 'https://')):
                        url = urljoin(self.base_url, url)
                    
                    # 避免重复链接
                    if url not in article_links:
                        # 获取文章标题(如果存在)
                        title_elem = link.select_one('h2')
                        title = title_elem.get_text(strip=True) if title_elem else "未知标题"
                        
                        logger.info(f"找到文章(区域3): {title} -> {url}")
                        article_links.append(url)
                        
                        if len(article_links) >= max_articles:
                            break
        
        # 如果仍然找不到足够的文章，尝试更通用的选择器
        if len(article_links) < max_articles:
            logger.info("使用通用选择器查找文章链接")
            # 寻找所有包含h2标题的链接
            all_links = soup.select('a[href*="unite.ai"] h2')
            for title_elem in all_links:
                link = title_elem.parent
                while link and link.name != 'a':
                    link = link.parent
                
                if link and link.has_attr('href'):
                    url = link['href']
                    # 排除导航链接、分类链接等
                    if '/category/' in url or '#' in url:
                        continue
                        
                    # 确保URL完整
                    if not url.startswith(('http://', 'https://')):
                        url = urljoin(self.base_url, url)
                    
                    # 避免重复链接
                    if url not in article_links:
                        title = title_elem.get_text(strip=True)
                        logger.info(f"找到文章(通用选择器): {title} -> {url}")
                        article_links.append(url)
                        
                        if len(article_links) >= max_articles:
                            break
        
        # 限制返回数量
        article_links = article_links[:max_articles]
        
        logger.info(f"共找到{len(article_links)}个文章链接")
        for idx, url in enumerate(article_links):
            logger.info(f"文章{idx+1}: {url}")
        
        return article_links

    async def get_article_content(self, page: Page, url: str) -> Dict[str, Any]:
        """获取文章内容"""
        
        logger.info(f"获取文章内容: {url}")
        
        try:
            # 访问文章页面
            await page.goto(url, wait_until="networkidle")
            
            # 等待页面加载
            await page.wait_for_load_state("networkidle")
            
            # 获取页面HTML内容
            html_content = await page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 提取标题
            title_elem = soup.select_one('h1.entry-title, h1.post-title, div.mvp-post-title-wrap h1')
            title = title_elem.get_text(strip=True) if title_elem else "未知标题"
            logger.info(f"找到标题: {title}")
            
            # 提取作者
            author_elem = soup.select_one('.author-name a, .entry-author a, .post-author a, .author_info a, span.author_info')
            author = author_elem.get_text(strip=True) if author_elem else "未知作者"
            # 移除"By"前缀，如果存在
            if author.startswith("By "):
                author = author[3:]
            logger.info(f"找到作者: {author}")
            
            # 提取发布日期
            date_elem = soup.select_one('time.entry-date, .posted-on time, .post-date, span.mvp-cd-date')
            pub_date = ""
            if date_elem:
                if date_elem.has_attr('datetime'):
                    pub_date = date_elem['datetime']
                else:
                    pub_date = date_elem.get_text(strip=True)
            logger.info(f"找到发布日期: {pub_date}")
            
            # 提取文章内容 - 使用更新的选择器，支持Unite.ai的布局
            content_elem = soup.select_one('#mvp-content-main, .entry-content, .post-content, article .content')
            content = ""
            html_content_str = ""
            
            if content_elem:
                # 移除不需要的元素，如广告、相关文章等
                for unwanted in content_elem.select('.advertisement, .related-posts, .social-share, .ssblock, .gsp_f_b, .ssplayer_wrapper, .gsp_content_wrapper_set, script'):
                    unwanted.decompose()
                
                # 提取所有段落文本
                paragraphs = content_elem.select('p')
                if paragraphs:
                    # 合并所有段落文本
                    content = ' '.join([p.get_text(strip=True) for p in paragraphs])
                    # 保存HTML内容
                    html_content_str = ''.join(str(p) for p in paragraphs)
                else:
                    # 如果找不到段落，则使用全部内容
                    content = content_elem.get_text(strip=True)
                    html_content_str = str(content_elem)
                
                logger.info(f"提取到内容长度: {len(content)} 字符")
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
