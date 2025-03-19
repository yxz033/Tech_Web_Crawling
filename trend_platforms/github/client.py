from typing import Optional, List
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime
from model.platform_trends import GithubTrend

class GithubClient:
    """GitHub API客户端"""
    
    def __init__(self, config: dict):
        self.config = config
        self.url = config['url']
        self.max_items = config['max_items']
        
    async def get_trending_repos(self) -> List[GithubTrend]:
        """获取趋势仓库列表"""
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # 提取仓库信息
                repos = []
                for i, repo in enumerate(soup.select('article.Box-row')):
                    if i >= self.max_items:
                        break
                        
                    name_elem = repo.select_one('h1 a')
                    desc_elem = repo.select_one('p')
                    lang_elem = repo.select_one('span[itemprop="programmingLanguage"]')
                    stars_elem = repo.select_one('a.Link--muted')
                    
                    if not all([name_elem, desc_elem]):
                        continue
                        
                    name = name_elem.text.strip()
                    description = desc_elem.text.strip()
                    language = lang_elem.text.strip() if lang_elem else "Unknown"
                    stars = int(stars_elem.text.strip().replace(',', '')) if stars_elem else 0
                    url = f"https://github.com{name_elem['href']}"
                    
                    repo = GithubTrend(
                        rank=i+1,
                        name=name,
                        description=description,
                        url=url,
                        language=language,
                        stars=stars
                    )
                    repos.append(repo)
                    
                return repos 