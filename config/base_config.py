from typing import List, Dict

class BaseConfig:
    """基础配置类"""
    
    # 存储配置
    STORAGE_CONFIG = {
        'storage_path': './data',
        'news_directory': 'news',
        'trends_directory': 'trends',
        'reports_directory': 'reports'
    }
    
    # 调度器配置
    SCHEDULER_CONFIG = {
        'news_crawl_hour': 8,  # 每天8点爬取新闻
        'news_crawl_minute': 0,
        'weekly_report_day': 'sun',  # 每周日生成周报
        'weekly_report_hour': 20,
        'weekly_report_minute': 0
    }
    
    # 新闻网站配置
    NEWS_SITES = {
        # HowToGeek
        'howtogeek': {
            'name': 'HowToGeek',
            'base_url': 'https://www.howtogeek.com/', # 请勿修改
            'latest_url': 'https://www.howtogeek.com/news/', # 请勿修改
            'max_articles': 10,  # 每次最多爬取10篇文章
            'search_keywords': ['deepseek', 'chatgpt', 'ai', 'llm', 'claude', 'gemini']
        },
        # UniteAI
        'uniteai': {
            'name': 'UniteAI',
            'base_url': 'https://www.unite.ai/',
            'latest_url': 'https://www.unite.ai', # 请勿修改
            'max_articles': 10,  # 每次最多爬取10篇文章
            'search_keywords': ['deepseek', 'deekseek', 'chatgpt']
        },
        # MarkTechPost
        'marktechpost': {
            'name': 'MarkTechPost',
            'base_url': 'https://www.marktechpost.com/',
            'latest_url': 'https://www.marktechpost.com/category/tech-news/', # 请勿修改
            'max_articles': 3,  # 每次最多爬取10篇文章
            'search_keywords': ['deepseek'] # 示例：['deepseek', 'chatgpt', 'claude', 'gemini', 'llama']
        }
    }
    
    # 趋势网站配置
    TREND_SITES = {
        # GitHub Trending
        'github': {
            'name': 'GitHub',
            'trending_url': 'https://github.com/trending',
            'languages': ['python', 'javascript']  # 要爬取的语言趋势
        }
    }
    
    # 趋势平台配置
    TREND_PLATFORMS = {
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