import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


def fetch_github_trending(languages: List[str] = None, time_range: str = "weekly") -> List[Dict]:
    """
    获取 GitHub Trending 项目
    
    Args:
        languages: 编程语言列表
        time_range: 时间范围 (daily, weekly, monthly)
    
    Returns:
        趋势项目列表
    """
    projects = []
    base_url = "https://github.com/trending"
    
    params = {
        "since": time_range
    }
    
    if not languages:
        languages = ["Python", "TypeScript"]
    
    for lang in languages:
        params["spoken_language_code"] = ""
        
        try:
            url = f"{base_url}/{lang}"
            logger.info(f"Fetching GitHub Trending: {url}")
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "lxml")
            articles = soup.select("article.box-shadow")
            
            for article in articles[:5]:
                try:
                    title_elem = article.select_one("h2 a")
                    if not title_elem:
                        continue
                    
                    full_name = title_elem.get("href", "").strip("/")
                    
                    desc_elem = article.select_one("p")
                    description = desc_elem.text.strip() if desc_elem else ""
                    
                    stars_elem = article.select_one("span.d-inline-block.float-sm-right")
                    stars = stars_elem.text.strip() if stars_elem else "0"
                    
                    lang_elem = article.select_one("span[itemprop='programmingLanguage']")
                    language = lang_elem.text.strip() if lang_elem else lang
                    
                    projects.append({
                        "full_name": full_name,
                        "description": description,
                        "stars": stars,
                        "language": language,
                        "url": f"https://github.com/{full_name}"
                    })
                except Exception as e:
                    logger.warning(f"Error parsing project: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error fetching GitHub Trending for {lang}: {e}")
    
    logger.info(f"Fetched {len(projects)} projects from GitHub Trending")
    return projects


def format_project_for_ai(project: Dict) -> str:
    """
    格式化项目信息用于 AI 摘要
    """
    return f"""项目: {project['full_name']}
语言: {project['language']}
Stars: {project['stars']}
描述: {project['description'][:200]}"""
