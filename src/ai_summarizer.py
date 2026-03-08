import os
import logging
from typing import List, Dict
import aiohttp
import asyncio

logger = logging.getLogger(__name__)


class AISummarizer:
    """AI 摘要生成器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.provider = config.get("provider", "siliconflow")
        self.base_url = config.get("base_url", "https://api.siliconflow.cn/v1")
        self.model = config.get("model", "Qwen/Qwen2.5-7B-Instruct")
        self.temperature = config.get("temperature", 0.7)
        
        api_key = os.getenv("AI_API_KEY")
        if not api_key:
            logger.warning("AI_API_KEY not found in environment variables")
        
        self.api_key = api_key
    
    async def _call_api(self, messages: List[Dict]) -> str:
        """调用 AI API"""
        if not self.api_key:
            return "AI API Key 未配置"
        
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": 1000
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=60) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["choices"][0]["message"]["content"]
                    else:
                        error_text = await response.text()
                        logger.error(f"API error: {response.status} - {error_text}")
                        return f"API 错误: {response.status}"
        except Exception as e:
            logger.error(f"Error calling AI API: {e}")
            return f"调用失败: {str(e)}"
    
    async def summarize_paper(self, paper_info: str) -> str:
        """对论文生成摘要"""
        system_prompt = """你是一个AI技术论文助手。请简洁地总结以下论文信息，提取关键技术点和创新点。
要求：
1. 用中文输出
2. 控制在100字以内
3. 突出技术亮点和实际应用价值"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": paper_info}
        ]
        
        return await self._call_api(messages)
    
    async def summarize_projects(self, projects_info: str) -> str:
        """对 GitHub 项目生成摘要"""
        system_prompt = """你是一个技术趋势分析师。请总结以下GitHubTrending项目，找出共同的技术趋势。
要求：
1. 用中文输出
2. 控制在150字以内
3. 分析技术方向和亮点"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": projects_info}
        ]
        
        return await self._call_api(messages)
    
    async def summarize_single_project(self, project_info: str) -> str:
        """对单个 GitHub 项目生成点评"""
        system_prompt = """你是一个技术评论员。请简洁点评以下GitHub项目，突出其亮点和适用场景。
要求：
1. 用中文输出
2. 控制在50字以内
3. 客观有见地"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": project_info}
        ]
        
        return await self._call_api(messages)
    
    async def summarize_papers_overall(self, papers_info: str) -> str:
        """对多篇论文生成整体趋势总结"""
        system_prompt = """你是一个AI技术趋势分析师。请分析以下多篇论文，总结整体技术趋势和研究方向。
要求：
1. 用中文输出
2. 控制在150字以内
3. 归纳共性技术方向"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": papers_info}
        ]
        
        return await self._call_api(messages)
    
    async def summarize_weekly(self, papers_summary: str, projects_summary: str) -> str:
        """生成周报摘要"""
        system_prompt = """你是一个科技周报编辑。请根据以下内容生成一份简洁的周报摘要。
要求：
1. 用中文输出
2. 控制在200字以内
3. 突出本周重点技术和趋势"""
        
        content = f"""## arXiv 论文亮点
{papers_summary}

## GitHub 趋势项目
{projects_summary}"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ]
        
        return await self._call_api(messages)


def create_summarizer(config: Dict) -> AISummarizer:
    """创建 AI 摘要生成器"""
    return AISummarizer(config)
