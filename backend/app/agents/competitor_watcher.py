"""
Agent #1 - Competitor Release Watcher.

Tracks competitor sites (blogs, changelogs, docs release notes)
and summarizes product/platform releases.
"""

from app.agents.base_agent import BaseAgent
from app.models.source import Source

HIGH_IMPACT_KEYWORDS = [
    "generally available",
    "GA",
    "pricing",
    "API",
    "security",
    "deprecation",
    "breaking change",
    "new model",
    "launch",
    "enterprise",
    "free tier",
    "rate limit",
]


class CompetitorWatcher(BaseAgent):

    @property
    def agent_type(self) -> str:
        return "competitor"

    def _get_content_type(self) -> str:
        return "competitor release note / blog post"

    async def discover_urls(self, source: Source) -> list[str]:
        return [source.url]

    async def post_process_finding(
        self, finding: dict, extraction, source: Source,
    ) -> dict:
        text = f"{finding.get('summary', '')} {finding.get('content', '')}".lower()

        impact_matches = [kw for kw in HIGH_IMPACT_KEYWORDS if kw.lower() in text]
        if impact_matches:
            finding["confidence"] = min(finding.get("confidence", 0.5) + 0.1, 1.0)

        return finding
