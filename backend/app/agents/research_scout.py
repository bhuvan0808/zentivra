"""
Agent #3 - Research Publication Scout.

Scans arXiv, Semantic Scholar, OpenReview, and curated research lab blogs
for the latest AI/ML research publications.
"""

import re
from datetime import datetime, timezone
from typing import Optional

from app.utils.logger import logger

from app.agents.base_agent import BaseAgent
from app.core.extractor import FeedEntry
from app.models.source import Source

# Relevance keywords from spec
RELEVANCE_KEYWORDS = {
    "benchmark": 2,
    "evaluation": 2,
    "agent": 3,
    "multimodal": 2,
    "reasoning": 2,
    "safety": 2,
    "alignment": 2,
    "data-centric": 2,
    "scaling": 2,
    "efficient": 1,
    "fine-tuning": 1,
    "instruction tuning": 2,
    "reinforcement learning from human feedback": 3,
    "RLHF": 3,
    "chain-of-thought": 2,
    "in-context learning": 2,
    "retrieval augmented": 2,
    "RAG": 2,
    "tool use": 2,
    "function calling": 2,
    "SOTA": 3,
    "state-of-the-art": 3,
    "large language model": 2,
    "LLM": 2,
    "foundation model": 2,
    "transformer": 1,
}


class ResearchScout(BaseAgent):
    """
    Agent #3: Research Publication Scout.

    Sources: arXiv (CS.CL, CS.LG, stat.ML), Semantic Scholar,
    OpenReview, curated research lab blogs.

    Outputs: Core contribution, novelty vs prior work,
    practical implications, relevance score.
    """

    @property
    def agent_type(self) -> str:
        return "research"

    def _get_content_type(self) -> str:
        return "research publication / academic paper"

    async def discover_urls(self, source: Source) -> list[str]:
        """
        Discover research paper URLs.

        For arXiv: Uses RSS feeds to get recent papers.
        For Semantic Scholar: Uses API search.
        For others: RSS or direct URL.
        """
        urls = []

        if "arxiv.org" in source.url and source.feed_url:
            # arXiv RSS feed
            feed_urls = await self._discover_from_feed(source.feed_url)
            urls.extend(feed_urls[:15])  # More papers for research

        elif "semanticscholar" in source.url:
            # Semantic Scholar API
            api_urls = await self._discover_from_semantic_scholar(source)
            urls.extend(api_urls)

        elif source.feed_url:
            feed_urls = await self._discover_from_feed(source.feed_url)
            urls.extend(feed_urls[:10])

        else:
            urls.append(source.url)

        return urls

    async def _discover_from_semantic_scholar(
        self, source: Source, limit: int = 10
    ) -> list[str]:
        """Query Semantic Scholar API for recent AI papers."""
        try:
            from app.config import settings

            # Build search query from keywords
            keywords = source.keywords or ["large language model", "foundation model"]
            query = " | ".join(keywords[:3])

            params = {
                "query": query,
                "limit": limit,
                "fields": "title,url,abstract,year,citationCount",
                "sort": "publicationDate:desc",
            }

            headers = {}
            if settings.semantic_scholar_api_key:
                headers["x-api-key"] = settings.semantic_scholar_api_key

            import httpx

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
                    urls = []
                    for paper in papers:
                        url = paper.get("url")
                        if url:
                            urls.append(url)
                    logger.info(
                        "semantic_scholar_results query=%s results=%d",
                        query,
                        len(urls),
                    )
                    return urls
                else:
                    logger.warning(
                        "semantic_scholar_error status=%d",
                        resp.status_code,
                    )
                    return []

        except Exception as e:
            logger.error("semantic_scholar_error error=%s", str(e))
            return []

    async def post_process_finding(
        self, finding: dict, extraction, source: Source
    ) -> dict:
        """
        Enrich research findings with:
        - Relevance score based on topic keywords
        - Research-specific category
        - Paper metadata (arXiv ID, authors)
        """
        finding["category"] = "research"
        finding["publisher"] = source.name

        # Compute keyword-based relevance score
        text = f"{finding.get('title', '')} {finding.get('summary_short', '')}".lower()
        relevance_score = 0
        matched_topics = []

        for keyword, weight in RELEVANCE_KEYWORDS.items():
            if keyword.lower() in text:
                relevance_score += weight
                matched_topics.append(keyword)

        # Normalize to 0-1 range (max theoretical ~30)
        normalized_relevance = min(relevance_score / 15.0, 1.0)

        # Adjust confidence based on relevance
        if normalized_relevance > 0.5:
            finding["confidence"] = min(finding["confidence"] + 0.1, 1.0)
        elif normalized_relevance < 0.2:
            finding["confidence"] = max(finding["confidence"] - 0.1, 0.1)

        # Add matched research topics as tags
        tags = finding.get("tags", [])
        tags.extend(matched_topics)
        tags.append("research_paper")
        finding["tags"] = list(set(tags))

        # Extract arXiv ID if present
        source_url = finding.get("source_url", "")
        arxiv_match = re.search(r"arxiv\.org/abs/(\d+\.\d+)", source_url)
        if arxiv_match:
            entities = finding.get("entities", {})
            entities["arxiv_id"] = arxiv_match.group(1)
            finding["entities"] = entities

        return finding
