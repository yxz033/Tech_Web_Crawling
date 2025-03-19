import asyncio
import logging
import warnings
import sys
import argparse
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config.base_config import BaseConfig
from base.base_crawler import AbstractCrawler
from news_sites.howtogeek import HowToGeekCrawler
from news_sites.uniteai import UniteAICrawler
from store.json import JSONStore

# 添加警告过滤，抑制Windows平台上asyncio的管道关闭警告
if sys.platform.startswith('win'):
    # 过滤asyncio的ResourceWarning
    warnings.filterwarnings("ignore", message="unclosed.*<_ProactorBasePipeTransport.*>", 
                           category=ResourceWarning)
    warnings.filterwarnings("ignore", message="unclosed.*<_OverlappedFuture.*>", 
                           category=ResourceWarning)
    warnings.filterwarnings("ignore", message="unclosed.*<asyncio.streams.StreamWriter.*>", 
                           category=ResourceWarning)
    
    # 设置proactor的事件循环策略
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TechTrendCrawler:
    """科技趋势爬虫主类"""
    
    def __init__(self):
        self.config = BaseConfig()
        self.scheduler = AsyncIOScheduler()
        self.store = JSONStore(self.config.STORAGE_CONFIG)
        
    async def crawl_news_sites(self):
        """爬取新闻网站"""
        logger.info("开始爬取新闻网站...")
        # TODO: 实现新闻网站爬取逻辑
        pass
        
    async def crawl_trends(self):
        """爬取趋势榜单"""
        logger.info("开始爬取趋势榜单...")
        # TODO: 实现趋势榜单爬取逻辑
        pass
        
    async def generate_weekly_report(self):
        """生成周报"""
        logger.info("开始生成周报...")
        # TODO: 实现周报生成逻辑
        pass
        
    async def test_howtogeek(self):
        """测试HowToGeek爬虫"""
        try:
            logger.info("开始测试HowToGeek爬虫...")
            
            # 创建HowToGeek爬虫实例
            crawler = HowToGeekCrawler(self.config.NEWS_SITES['howtogeek'])
            
            # 初始化浏览器
            await crawler.init_browser()
            
            try:
                # 爬取文章
                articles = await crawler.crawl()
                logger.info(f"爬取到{len(articles)}篇文章")
                
                # 保存文章
                if articles:
                    await self.store.save_articles(articles)
                    logger.info("文章保存成功")
                    
                    # 打印第一篇文章的信息作为示例
                    if articles:
                        first_article = articles[0]
                        logger.info("\n第一篇文章信息:")
                        logger.info(f"标题: {first_article.title}")
                        logger.info(f"作者: {first_article.author}")
                        logger.info(f"发布时间: {first_article.published_date}")
                        logger.info(f"链接: {first_article.url}")
                
            finally:
                # 关闭浏览器
                await crawler.close_browser()
                
        except Exception as e:
            logger.error(f"测试HowToGeek爬虫时出错: {str(e)}")
            raise
            
    async def test_uniteai(self):
        """测试UniteAI爬虫"""
        try:
            logger.info("开始测试UniteAI爬虫...")
            
            # 创建UniteAI爬虫实例
            crawler = UniteAICrawler(self.config.NEWS_SITES['uniteai'])
            
            # 初始化浏览器
            await crawler.init_browser()
            
            try:
                # 爬取文章
                articles = await crawler.crawl()
                logger.info(f"爬取到{len(articles)}篇文章")
                
                # 保存文章
                if articles:
                    await self.store.save_articles(articles)
                    logger.info("文章保存成功")
                    
                    # 打印第一篇文章的信息作为示例
                    if articles:
                        first_article = articles[0]
                        logger.info("\n第一篇文章信息:")
                        logger.info(f"标题: {first_article.title}")
                        logger.info(f"作者: {first_article.author}")
                        logger.info(f"发布时间: {first_article.published_date}")
                        logger.info(f"链接: {first_article.url}")
                
            finally:
                # 关闭浏览器
                await crawler.close_browser()
                
        except Exception as e:
            logger.error(f"测试UniteAI爬虫时出错: {str(e)}")
            raise

    def configure_schedules(self):
        """配置定时任务"""
        # 每日爬取新闻网站
        self.scheduler.add_job(
            self.crawl_news_sites,
            'cron',
            hour=self.config.SCHEDULER_CONFIG['news_crawl_hour'],
            minute=self.config.SCHEDULER_CONFIG['news_crawl_minute']
        )
        
        # 每小时爬取趋势榜单
        self.scheduler.add_job(
            self.crawl_trends,
            'interval',
            hours=1
        )
        
        # 每周日生成周报
        self.scheduler.add_job(
            self.generate_weekly_report,
            'cron',
            day_of_week=self.config.SCHEDULER_CONFIG['weekly_report_day'],
            hour=self.config.SCHEDULER_CONFIG['weekly_report_hour'],
            minute=self.config.SCHEDULER_CONFIG['weekly_report_minute']
        )
        
    async def start(self):
        """启动爬虫"""
        try:
            logger.info("正在启动爬虫...")
            self.configure_schedules()
            self.scheduler.start()
            
            # 立即执行一次爬取
            await self.crawl_news_sites()
            await self.crawl_trends()
            
            # 保持程序运行
            while True:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"爬虫运行出错: {str(e)}")
            self.scheduler.shutdown()
            raise

async def main():
    """程序入口"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='科技趋势爬虫')
    parser.add_argument('platform', nargs='?', default='all', 
                        choices=['all', 'howtogeek', 'uniteai'], 
                        help='要爬取的平台: howtogeek, uniteai或all(默认)')
    args = parser.parse_args()
    
    crawler = TechTrendCrawler()
    
    # 根据命令行参数选择爬取平台
    if args.platform == 'all' or args.platform == 'howtogeek':
        await crawler.test_howtogeek()
    
    if args.platform == 'all' or args.platform == 'uniteai':
        await crawler.test_uniteai()

async def cleanup_resources():
    """清理异步资源"""
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    await asyncio.sleep(0.5)  # 等待足够长的时间以确保资源被释放

if __name__ == "__main__":
    try:
        # 使用asyncio.run运行异步主函数
        asyncio.run(main())
    except KeyboardInterrupt:
        # 处理Ctrl+C中断
        logger.info("程序被用户中断")
    finally:
        try:
            # 运行清理函数直接在当前线程的新事件循环中
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(cleanup_resources())
            loop.close()
        except Exception as e:
            logger.error(f"清理资源时出错: {e}") 