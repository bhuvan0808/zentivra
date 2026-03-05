"""
Agent #1 - Competitor Release Watcher.

Tracks competitor sites (blogs, changelogs, docs release notes)
and summarizes product/platform releases.
"""

from app.utils.logger import logger

from app.agents.base_agent import BaseAgent
from app.models.source import Source

# Keywords that indicate high-impact releases
HIGH_IMPACT_KEYWORDS = [
    "generally available", "GA", "pricing", "API", "security",
    "deprecation", "breaking change", "new model", "launch",
    "enterprise", "free tier", "rate limit",
]


class CompetitorWatcher(BaseAgent):
    """
    Agent #1: Competitor Release Watcher.

    Discovers pages via RSS → sitemap → crawl, fetches page content,
    extracts canonical text, detects changes via diff, summarizes changes,
    and ranks impact (GA/pricing/API/security mentions).
    """

    @property
    def agent_type(self) -> str:
        return "competitor"

    def _get_content_type(self) -> str:
        return "competitor release note / blog post"

    async def discover_urls(self, source: Source) -> list[str]:
        """
        Discover URLs from RSS feeds, sitemaps, or direct crawl.

        Priority: RSS feed → direct URL
        """
        urls = []

        # Try RSS feed first (most reliable for blogs)
        if source.feed_url:
            feed_urls = await self._discover_from_feed(source.feed_url)
            urls.extend(feed_urls)
            logger.info(
                "competitor_feed_discovered source=%s urls=%d",
                source.name,
                len(feed_urls),
            )

        # Fallback to direct URL
        if not urls:
            urls.append(source.url)

        return urls[:10]  # Cap at 10 URLs per source

    async def post_process_finding(
        self, finding: dict, extraction, source: Source
    ) -> dict:
        """
        Enrich competitor findings with impact signals.

        - Boost confidence for high-impact keywords
        - Add competitor-specific tags
        """
        text = f"{finding.get('title', '')} {finding.get('summary_short', '')}".lower()

        # Check for high-impact keywords
        impact_matches = [kw for kw in HIGH_IMPACT_KEYWORDS if kw.lower() in text]
        if impact_matches:
            # Boost confidence for high-impact releases
            finding["confidence"] = min(finding["confidence"] + 0.1, 1.0)
            finding["tags"] = list(set(finding.get("tags", []) + impact_matches))

        # Ensure publisher is set
        finding["publisher"] = source.name

        # Add competitor entity
        entities = finding.get("entities", {})
        companies = entities.get("companies", [])
        if source.name not in companies:
            companies.append(source.name)
        entities["companies"] = companies
        finding["entities"] = entities

        return finding
