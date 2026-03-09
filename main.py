import os
import sys
import asyncio
import logging
import yaml
from datetime import datetime
from typing import Dict, List

sys.path.insert(0, os.path.dirname(__file__))

from src.arxiv_fetcher import fetch_arxiv_papers, get_paper_abstract
from src.github_trending import fetch_github_trending, format_project_for_ai
from src.ai_summarizer import create_summarizer
from src.dingtalk import create_notifier

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config(mode: str = "daily") -> Dict:
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    
    if not os.path.exists(config_path):
        logger.warning("config.yaml not found, using default config")
        return {
            "ai": {
                "provider": "siliconflow",
                "base_url": "https://api.siliconflow.cn/v1",
                "model": "Qwen/Qwen2.5-7B-Instruct",
                "temperature": 0.7
            },
            "arxiv": {
                "keywords": ["machine learning", "deep learning"],
                "max_results": 5,
                "categories": ["cs.AI", "cs.LG"]
            },
            "github_trending": {
                "languages": ["Python", "TypeScript"],
                "time_range": "daily" if mode == "daily" else "weekly"
            },
            "report": {
                "title": "AI & Tech 日报" if mode == "daily" else "AI & Tech 周报",
                "output_file": "daily_report.md" if mode == "daily" else "weekly_report.md"
            },
            "dingtalk": {}
        }
    
    with open(config_path, "r", encoding="utf-8") as f:
        base_config = yaml.safe_load(f)
    
    if mode == "daily":
        base_config["github_trending"]["time_range"] = "daily"
        base_config["report"]["title"] = base_config.get("report", {}).get("daily_title", "AI & Tech 日报")
        base_config["report"]["output_file"] = "daily_report.md"
    else:
        base_config["github_trending"]["time_range"] = "weekly"
        base_config["report"]["title"] = base_config.get("report", {}).get("title", "AI & Tech 周报")
        base_config["report"]["output_file"] = "weekly_report.md"
    
    return base_config


async def generate_report(mode: str = "daily"):
    """生成报告"""
    logger.info(f"Starting {mode} report generation...")
    
    config = load_config(mode)
    
    papers = fetch_arxiv_papers(
        keywords=config["arxiv"]["keywords"],
        max_results=config["arxiv"]["max_results"],
        categories=config["arxiv"].get("categories")
    )
    logger.info(f"Fetched {len(papers)} papers")
    
    projects = fetch_github_trending(
        languages=config["github_trending"]["languages"],
        time_range=config["github_trending"]["time_range"],
        topics=config["github_trending"].get("topics")
    )
    logger.info(f"Fetched {len(projects)} projects")
    
    summarizer = create_summarizer(config["ai"])
    
    papers_details = ""
    papers_summary = ""
    projects_details = ""
    projects_summary = ""
    overall_summary = ""
    
    if papers and projects and os.getenv("AI_API_KEY"):
        logger.info("Generating paper summaries with AI...")
        papers_info = "\n\n".join([get_paper_abstract(p) for p in papers[:5]])
        papers_result = await summarizer.summarize_papers_batch(papers_info)
        
        for i, paper in enumerate(papers[:5]):
            summary = papers_result[i].get("summary", "") if i < len(papers_result) else ""
            papers_details += f"{i+1}. **{paper['title'][:60]}**\n   - 摘要: {summary}\n   - [论文链接](http://arxiv.org/abs/{paper['arxiv_id']})\n\n"
        
        logger.info("Generating paper trend with AI...")
        papers_summary = await summarizer.summarize_papers_overall(papers_info)
        
        logger.info("Generating project reviews with AI...")
        projects_info = "\n\n".join([format_project_for_ai(p) for p in projects[:10]])
        projects_result = await summarizer.summarize_projects_batch(projects_info)
        
        for i, project in enumerate(projects[:10]):
            summary = projects_result[i].get("summary", "") if i < len(projects_result) else ""
            projects_details += f"{i+1}. **[{project['full_name']}]({project['url']})** ({project['stars']} stars)\n   - {project['description'][:200]}\n   - 点评: {summary}\n\n"
        
        logger.info("Generating project trend with AI...")
        projects_summary = await summarizer.summarize_projects(projects_info)
        
        logger.info("Generating overall summary with AI...")
        overall_summary = await summarizer.summarize_overall(papers_details, projects_details, papers_summary, projects_summary)
    
    if not os.getenv("AI_API_KEY"):
        papers_details = "\n".join([f"- [{p['title']}](http://arxiv.org/abs/{p['arxiv_id']})" for p in papers[:5]])
        projects_details = "\n".join([f"- [{p['full_name']}]({p['url']}) ({p['stars']} stars)" for p in projects[:10]])
    
    title = config["report"]["title"]
    week_num = datetime.now().isocalendar()[1]
    
    time_range_str = "每日" if mode == "daily" else "每周"
    report_content = f"""### ⭐ GitHub Trending ({len(projects)}个)

{projects_details}

**📊 项目整体趋势:**
{projects_summary}

### 📚 arXiv 论文 ({len(papers)}篇)

{papers_details}

**📊 论文整体趋势:**
{papers_summary}

**📝 整体总结:**
{overall_summary}

---
📅 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')} | 第{week_num}周 | {time_range_str}趋势"""
    
    markdown_file = config["report"]["output_file"]
    with open(markdown_file, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write(report_content)
    
    logger.info(f"Report saved to {markdown_file}")
    
    notifier = create_notifier(config.get("dingtalk"))
    if notifier.webhook:
        logger.info("Sending report to DingTalk...")
        notifier.send_weekly_report(title, report_content)
    else:
        logger.warning("DingTalk webhook not configured, skipping notification")
    
    return markdown_file


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "daily"
    asyncio.run(generate_report(mode))
