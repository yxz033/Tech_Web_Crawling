from typing import List, Dict

class BaseConfig:
    """基础配置类"""
    
    # 新闻网站配置
    NEWS_SITES = {
        'howtogeek': {
            'url': 'https://www.howtogeek.com',
            'latest_url': 'https://www.howtogeek.com/news/',
            'max_articles': 2,
            'search_keywords': ['deepseek']  # 添加搜索关键词列表字段，示例：['deepseek', 'Cursor']   
        },
        'uniteai': {
            'url': 'https://www.unite.ai',
            'latest_url': 'https://www.unite.ai',
            'max_articles': 2,
            'search_keywords': ['Nvidia', 'deepseek', 'chatgpt']  # 添加deepseek和deekseek作为搜索关键词
        },
        'marktechpost': {
            'url': 'https://www.marktechpost.com',
            'latest_url': 'https://www.marktechpost.com/category/artificial-intelligence/',
            'max_articles': 10,
            'search_keywords': []  # 添加搜索关键词列表字段，示例：['deepseek', 'Cursor']   
        },
        'the_decoder': {
            'url': 'https://the-decoder.com',
            'latest_url': 'https://the-decoder.com/news/',
            'max_articles': 10,
            'search_keywords': []  # 添加搜索关键词列表字段，示例：['deepseek', 'Cursor']   
        }
    }
    
    # 趋势平台配置
    TREND_PLATFORMS = {
        'github': {
            'url': 'https://github.com/trending',
            'max_items': 25
        },
        'twitter': {
            'url': 'https://twitter.com/explore/tabs/trending',
            'max_items': 25
        },
        'huggingface': {
            'url': 'https://huggingface.co/models?sort=trending',
            'max_items': 25
        }
    }
    
    # 爬虫配置
    CRAWLER_CONFIG = {
        'request_delay': 2,  # 请求间隔(秒)
        'timeout': 30,       # 请求超时时间
        'retry_times': 3,    # 重试次数
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # 数据存储配置
    STORAGE_CONFIG = {
        'type': 'json',  # 改为json类型,更简单易用
        'mysql': {
            'host': 'localhost',
            'port': 3306,
            'user': 'root',
            'password': '',
            'database': 'tech_trends'
        },
        'csv_path': 'data/articles.csv',
        'json_path': 'data/articles.json'
    }
    
    # 定时任务配置
    SCHEDULER_CONFIG = {
        'news_crawl_hour': 0,    # 新闻爬取时间(24小时制)
        'news_crawl_minute': 0,  # 新闻爬取分钟
        'trend_crawl_interval': 3600,  # 趋势爬取间隔(秒)
        'weekly_report_day': 'sun',     # 周报生成日期
        'weekly_report_hour': 0,        # 周报生成时间
        'weekly_report_minute': 0       # 周报生成分钟
    } 