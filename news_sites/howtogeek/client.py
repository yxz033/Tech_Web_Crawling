from typing import Optional, List, Dict, Any, Tuple
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import logging
from model.news_article import NewsArticle
from urllib.parse import urljoin
from playwright.async_api import Page
import asyncio
import warnings
import sys

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

class HowToGeekClient:
    """HowToGeek API客户端"""
    
    def __init__(self, config: dict):
        self.config = config
        self.base_url = config['url']
        self.latest_url = config['latest_url']
        self.max_articles = config['max_articles']
        
    async def get_latest_articles(self, page: Page, max_articles: int) -> List[str]:
        """获取最新文章链接"""
        
        logger.info(f"获取HowToGeek最新文章链接，最大数量: {max_articles}")
        
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
        
        # 1. 首先尝试查找网页截图中的第一个元素示例：.bc-title-link
        logger.info("尝试查找.bc-title-link元素...")
        title_links = soup.select('a.bc-title-link')
        logger.info(f"找到{len(title_links)}个a.bc-title-link元素")
        
        for link in title_links:
            if link.has_attr('href') and link.has_attr('title'):
                url = link['href']
                title = link['title']
                logger.info(f"找到标题链接: {title} -> {url}")
                
                # 确保URL完整
                if not url.startswith(('http://', 'https://')):
                    url = urljoin(self.base_url, url)
                
                if url not in article_links:
                    article_links.append(url)
        
        # 2. 尝试查找网页截图中的第三个元素示例：.w-display-card-content.regular.article-block
        if len(article_links) < max_articles:
            logger.info("尝试查找.w-display-card-content元素...")
            display_cards = soup.select('.w-display-card-content')
            logger.info(f"找到{len(display_cards)}个.w-display-card-content元素")
            
            for card in display_cards:
                # 查找display-card中的标题链接
                title_link = card.select_one('.display-card-title a, h5 a')
                if title_link and title_link.has_attr('href'):
                    url = title_link['href']
                    title = title_link.get_text(strip=True)
                    logger.info(f"找到display-card标题链接: {title} -> {url}")
                    
                    # 确保URL完整
                    if not url.startswith(('http://', 'https://')):
                        url = urljoin(self.base_url, url)
                    
                    if url not in article_links:
                        article_links.append(url)
        
        # 3. 尝试更通用的选择器
        if len(article_links) < max_articles:
            logger.info("尝试查找其他可能的文章链接...")
            
            # 查找h5标题中的链接
            h5_links = soup.select('h5 a')
            for link in h5_links:
                if link.has_attr('href'):
                    url = link['href']
                    title = link.get_text(strip=True)
                    
                    # 确保URL完整
                    if not url.startswith(('http://', 'https://')):
                        url = urljoin(self.base_url, url)
                    
                    if url not in article_links:
                        article_links.append(url)
                        logger.info(f"找到h5链接: {title} -> {url}")
            
            # 查找包含"article"类的div中的链接
            article_divs = soup.select('div[class*="article"] a, .article a')
            for link in article_divs:
                if link.has_attr('href'):
                    url = link['href']
                    # 过滤一些非文章链接
                    if '/tag/' in url or '#' in url or 'javascript:' in url:
                        continue
                    
                    # 确保URL完整
                    if not url.startswith(('http://', 'https://')):
                        url = urljoin(self.base_url, url)
                    
                    if url not in article_links and 'howtogeek.com' in url:
                        article_links.append(url)
                        logger.info(f"找到article div中的链接: {url}")
        
        # 4. 最后的尝试：直接执行JavaScript获取所有链接
        if len(article_links) < max_articles:
            logger.info("执行JavaScript获取所有链接...")
            
            # 执行JavaScript获取所有链接
            links_js = await page.evaluate("""
                () => {
                    const links = [];
                    document.querySelectorAll('a[href*="/"]').forEach(link => {
                        if (link.href && 
                            !link.href.includes('/tag/') && 
                            !link.href.includes('#') && 
                            !link.href.includes('javascript:') &&
                            link.href.includes('howtogeek.com')) {
                            links.push({
                                url: link.href,
                                text: link.innerText.trim()
                            });
                        }
                    });
                    return links;
                }
            """)
            
            for link_info in links_js:
                url = link_info.get('url', '')
                text = link_info.get('text', '')
                
                # 过滤一些特定的链接
                if (url and 
                    url not in article_links and 
                    '/tag/' not in url and
                    'howtogeek.com' in url and
                    text and len(text) > 5):  # 确保链接文本不是太短
                    
                    article_links.append(url)
                    logger.info(f"通过JS找到链接: {text} -> {url}")
                    
                    if len(article_links) >= max_articles:
                        break
        
        # 保存HTML内容以便调试
        if len(article_links) == 0:
            logger.warning("未找到任何文章链接，保存HTML以便分析")
            try:
                with open('howtogeek_debug.html', 'w', encoding='utf-8') as f:
                    f.write(html_content)
                logger.info("已保存HTML内容到howtogeek_debug.html")
            except Exception as e:
                logger.error(f"保存HTML时出错: {str(e)}")
        
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
            
            # 提取标题 - 尝试多种可能的选择器
            title = None
            title_selectors = [
                'h1.article-title', 'h1.entry-title', 'h1.post-title', 
                'h1[class*="title"]', 'header h1', 'h1'
            ]
            
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    logger.info(f"找到标题: {title}")
                    break
            
            if not title:
                logger.warning(f"无法提取文章标题: {url}")
                title = "未知标题"
            
            # 提取作者 - 尝试多种可能的选择器
            author = None
            author_selectors = [
                'a.article-author', '.article-author', 'a[rel="author"]', '.author-name', '.byline a', 
                '[itemprop="author"]', '.entry-meta .author', '.w-author-name a',
                '.article-byline-wrap a', '.w-display-card-meta .w-author a'
            ]
            
            for selector in author_selectors:
                author_elem = soup.select_one(selector)
                if author_elem:
                    author = author_elem.get_text(strip=True)
                    logger.info(f"找到作者: {author}")
                    break
            
            if not author:
                logger.warning(f"无法提取作者: {url}")
                author = "未知作者"
            
            # 提取发布日期 - 尝试多种可能的选择器
            pub_date = None
            date_selectors = [
                'time[datetime]', '[itemprop="datePublished"]', 
                '.entry-date', '.posted-on time', 'meta[property="article:published_time"]',
                '.article-date', '.w-display-card-meta .article-date', '.meta_txt.article-date time',
                '.w-display-card-date', 'time.display-card-date'
            ]
            
            for selector in date_selectors:
                date_elem = soup.select_one(selector)
                if date_elem:
                    # 首先尝试从datetime属性获取日期
                    if date_elem.has_attr('datetime'):
                        try:
                            date_str = date_elem['datetime']
                            pub_date = datetime.fromisoformat(date_str.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')
                            logger.info(f"从datetime属性找到日期: {pub_date}")
                            break
                        except Exception as e:
                            logger.warning(f"解析datetime属性时出错: {e}")
                    
                    # 如果从属性获取失败，尝试从文本内容获取
                    date_text = date_elem.get_text(strip=True)
                    pub_date = date_text
                    logger.info(f"找到日期文本: {pub_date}")
                    
                    # 处理相对时间格式，如"19 hours ago"
                    # 首先清理日期文本，移除"Published"前缀
                    clean_date_text = date_text.replace("Published", "").strip()
                    
                    if "hours ago" in clean_date_text or "hour ago" in clean_date_text:
                        try:
                            # 提取数字部分
                            hours_text = clean_date_text.split()[0]
                            hours_ago = int(hours_text)
                            pub_date = (datetime.now() - timedelta(hours=hours_ago)).strftime('%Y-%m-%d %H:%M:%S')
                            logger.info(f"处理相对时间，转换为: {pub_date}")
                        except Exception as e:
                            logger.warning(f"处理相对时间时出错: {e}")
                    elif "days ago" in clean_date_text or "day ago" in clean_date_text:
                        try:
                            days_text = clean_date_text.split()[0]
                            days_ago = int(days_text)
                            pub_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d %H:%M:%S')
                            logger.info(f"处理相对时间，转换为: {pub_date}")
                        except Exception as e:
                            logger.warning(f"处理相对时间时出错: {e}")
                    elif "minutes ago" in clean_date_text or "minute ago" in clean_date_text:
                        try:
                            minutes_text = clean_date_text.split()[0]
                            minutes_ago = int(minutes_text)
                            pub_date = (datetime.now() - timedelta(minutes=minutes_ago)).strftime('%Y-%m-%d %H:%M:%S')
                            logger.info(f"处理相对时间，转换为: {pub_date}")
                        except Exception as e:
                            logger.warning(f"处理相对时间时出错: {e}")
                    break
            
            if not pub_date:
                logger.warning(f"无法提取发布日期: {url}")
                pub_date = "未知日期"
            
            # 获取文章摘要（Summary部分）
            summary_html = ""
            summary_text = ""
            
            # 查找用户指定的Summary元素
            summary_elem = soup.select_one('div.emaki-custom.key-points')
            if summary_elem:
                # 保存HTML内容
                summary_html = str(summary_elem)
                
                # 提取文本内容
                summary_title = summary_elem.select_one('h3.title')
                summary_points = summary_elem.select('li')
                
                if summary_title:
                    summary_text += f"{summary_title.get_text(strip=True)}\n\n"
                
                if summary_points:
                    for point in summary_points:
                        summary_text += f"• {point.get_text(strip=True)}\n"
                    
                logger.info(f"找到Summary摘要，包含{len(summary_points)}个要点")
            
            # 提取正文内容
            content_text = ""
            paragraphs = []
            
            # 直接使用更有效的方法查找所有段落
            all_paragraphs = soup.select('article p, .article p, .content p, .post p, main p')
            if all_paragraphs:
                # 过滤掉footer和评论相关的段落
                filtered_paragraphs = []
                for p in all_paragraphs:
                    # 检查当前元素或其父元素是否包含article-footer类
                    if 'article-footer' in p.get('class', []) or any('article-footer' in parent.get('class', []) for parent in p.parents):
                        logger.info("检测到article-footer，停止获取内容")
                        break
                        
                    # 跳过footer和评论相关的段落
                    if p.parent and (p.parent.get('id', '') == 'comment-form' or 
                                    'footer' in p.parent.get('class', []) or
                                    'comment' in p.parent.get('class', []) or
                                    'article-footer' in p.parent.get('class', [])):
                        continue
                    
                    # 检查是否位于footer标签内
                    parent_footer = p.find_parent('footer')
                    if parent_footer:
                        continue
                        
                    # 检查是否在特定ID内
                    parent_footer_threads = p.find_parent(id='footer-threads')
                    if parent_footer_threads:
                        continue
                        
                    # 跳过特定的评论提示段落
                    if 'comment-submit-rules' in p.get('class', []):
                        continue
                        
                    filtered_paragraphs.append(p)
                
                paragraphs = filtered_paragraphs
                logger.info(f"找到{len(paragraphs)}个段落（已过滤）")
            
            # 提取段落文本，组合成文本内容
            if paragraphs:
                # 添加摘要作为内容开头
                if summary_text:
                    content_text = summary_text + "\n\n"
                
                # 添加段落内容
                content_text += '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                logger.info(f"生成文本内容，总长度: {len(content_text)}")
            else:
                logger.warning(f"无法提取文章内容: {url}")
                content_text = "无法获取内容"
            
            # 提取图片URL
            image_url = None
            img_selectors = [
                '.featured-image img', 'article img.wp-post-image', 
                'meta[property="og:image"]', 'article img:first-of-type',
                '.article-featured-image img', '.post-thumbnail img',
                '.w-display-card-image img', '.display-card-image img',
                '.article-image img', '.entry-content img:first-of-type'
            ]
            
            for selector in img_selectors:
                img_elem = soup.select_one(selector)
                if img_elem:
                    if selector == 'meta[property="og:image"]':
                        image_url = img_elem.get('content', '')
                    else:
                        image_url = img_elem.get('src', '')
                        # 如果没有src属性，尝试data-src属性（延迟加载的图片）
                        if not image_url:
                            image_url = img_elem.get('data-src', '')
                    
                    if image_url:
                        # 确保URL完整
                        if not image_url.startswith(('http://', 'https://')):
                            image_url = urljoin('https://www.howtogeek.com', image_url)
                        
                        logger.info(f"找到图片URL: {image_url}")
                        break
            
            # 如果通过选择器没找到图片，尝试在整个文档中查找图片
            if not image_url:
                all_imgs = soup.select('img[src], img[data-src]')
                for img in all_imgs:
                    image_url = img.get('src', img.get('data-src', ''))
                    if image_url and not image_url.startswith(('data:', 'javascript:')):
                        # 确保URL完整
                        if not image_url.startswith(('http://', 'https://')):
                            image_url = urljoin('https://www.howtogeek.com', image_url)
                        
                        logger.info(f"通过备用方法找到图片URL: {image_url}")
                        break
            
            if not image_url:
                logger.warning(f"无法提取图片URL: {url}")
            
            # 构建文章数据对象
            article = {
                'title': title,
                'author': author,
                'pub_date': pub_date,
                'content': content_text,  # 纯文本内容（包含摘要和段落）
                'url': url,
                'image_url': image_url,
                'source': 'howtogeek'
            }
            
            return article
            
        except Exception as e:
            logger.error(f"获取文章内容失败: {url}, 错误: {str(e)}", exc_info=True)
            return {
                'title': "获取失败",
                'author': "未知",
                'pub_date': "未知",
                'content': f"获取内容失败: {str(e)}",
                'url': url,
                'image_url': None,
                'source': 'howtogeek'
            }

async def main():
    """程序入口"""
    try:
        crawler = HowToGeekClient(config)
        await crawler.test_howtogeek()
    finally:
        # 确保关闭所有异步资源
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # 等待一小段时间确保资源完全释放
        await asyncio.sleep(0.1)

if __name__ == "__main__":
    asyncio.run(main()) 