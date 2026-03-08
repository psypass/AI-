import feedparser
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


def fetch_arxiv_papers(keywords: List[str], max_results: int = 10, categories: List[str] = None) -> List[Dict]:
    """
    从 arXiv 获取论文
    
    Args:
        keywords: 搜索关键词
        max_results: 最大结果数
        categories: arXiv 分类
    
    Returns:
        论文列表
    """
    papers = []
    
    search_query = " OR ".join([f"all:{kw}" for kw in keywords])
    if categories:
        cat_query = " OR ".join([f"cat:{cat}" for cat in categories])
        search_query = f"({search_query}) AND ({cat_query})"
    
    base_url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": search_query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }
    
    try:
        logger.info(f"Fetching arXiv papers with query: {search_query}")
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        
        feed = feedparser.parse(response.content)
        
        for entry in feed.entries[:max_results]:
            paper = {
                "title": entry.title.replace("\n", " ").strip(),
                "summary": entry.summary.replace("\n", " ").strip(),
                "authors": [author.name for author in entry.authors],
                "published": entry.published[:10],
                "pdf_url": None,
                "arxiv_id": entry.id.split("/")[-1],
            }
            
            for link in entry.links:
                if link.type == "application/pdf":
                    paper["pdf_url"] = link.href
                    break
            
            papers.append(paper)
            
        logger.info(f"Fetched {len(papers)} papers from arXiv")
        
    except Exception as e:
        logger.error(f"Error fetching arXiv papers: {e}")
    
    return papers


def get_paper_abstract(paper: Dict) -> str:
    """
    获取论文摘要（用于 AI 摘要）
    """
    return f"""标题: {paper['title']}

作者: {', '.join(paper['authors'][:3])}{'...' if len(paper['authors']) > 3 else ''}

发表日期: {paper['published']}

摘要: {paper['summary'][:500]}"""
