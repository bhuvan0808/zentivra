"""
Agent #3 - Research Publication Scout.

Scans arXiv, Semantic Scholar, and curated research lab blogs
for the latest AI/ML research publications.
"""

from app.agents.base_agent import BaseAgent
from app.models.source import Source
from app.utils.logger import logger

RELEVANCE_KEYWORDS = {
    "benchmark": 2, "evaluation": 2, "agent": 3, "multimodal": 2,
    "reasoning": 2, "safety": 2, "alignment": 2, "scaling": 2,
    "fine-tuning": 1, "instruction tuning": 2, "RLHF": 3,
    "chain-of-thought": 2, "in-context learning": 2, "RAG": 2,
    "tool use": 2, "function calling": 2, "SOTA": 3,
    "state-of-the-art": 3, "LLM": 2, "foundation model": 2,
    "transformer": 1,
}


class ResearchScout(BaseAgent):

    @property
    def agent_type(self) -> str:
        return "research"

    def _get_content_type(self) -> str:
        return "research publication / academic paper"

    async def discover_urls(self, source: Source) -> list[str]:
        urls = []

        if "semanticscholar" in source.url:
            api_urls = await self._discover_from_semantic_scholar(source)
            urls.extend(api_urls)
        else:
            urls.append(source.url)

        return urls

    async def _discover_from_semantic_scholar(
        self, source: Source, limit: int = 10,
    ) -> list[str]:
        try:
            from app.config import settings
            import httpx

            query = "large language model foundation model"
            params = {
                "query": query,
                "limit": limit,
                "fields": "title,url,abstract,year,citationCount",
                "sort": "publicationDate:desc",
            }
            headers = {}
            if settings.semantic_scholar_api_key:
                headers["x-api-key"] = settings.semantic_scholar_api_key

            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://api.semanticscholar.org/graph/v1/paper/search",
                    params=params,
                    headers=headers,
                    timeout=30,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    papers = data.get("data", [])
                    urls = [p["url"] for p in papers if p.get("url")]
                    logger.info("semantic_scholar_results count=%d", len(urls))
                    return urls
                else:
                    logger.warning("semantic_scholar_error status=%d", resp.status_code)
                    return []
        except Exception as exc:
            logger.error("semantic_scholar_error err=%s", str(exc)[:200])
            return []

    async def post_process_finding(
        self, finding: dict, extraction, source: Source,
    ) -> dict:
        finding["category"] = "research"

        text = f"{finding.get('summary', '')} {finding.get('content', '')}".lower()
        relevance_score = sum(
            weight for keyword, weight in RELEVANCE_KEYWORDS.items()
            if keyword.lower() in text
        )

        normalized = min(relevance_score / 15.0, 1.0)
        if normalized > 0.5:
            finding["confidence"] = min(finding.get("confidence", 0.5) + 0.1, 1.0)
        elif normalized < 0.2:
            finding["confidence"] = max(finding.get("confidence", 0.5) - 0.1, 0.1)

        return finding
