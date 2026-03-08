"""
Agent #1 - Competitor Release Watcher.

Domain focus: Monitors competitor companies for strategic intelligence.
Produces findings from competitor blogs, changelogs, docs release notes,
and product/platform announcements. Boosts confidence for high-impact
keywords (GA, pricing, API, security, deprecation, etc.).
"""

from app.agents.base_agent import BaseAgent
from app.models.source import Source

# Keywords that indicate high-impact competitor announcements
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
    """
    Monitors competitor companies for strategic intelligence.

    Specialization vs BaseAgent: Uses source.url directly (no custom URL
    discovery). Post-processes findings to boost confidence when high-impact
    keywords (GA, pricing, API, security, deprecation, etc.) are present.
    Content type: "competitor release note / blog post".
    """

    @property
    def agent_type(self) -> str:
        return "competitor"

    def _get_content_type(self) -> str:
        return "competitor release note / blog post"

    async def discover_urls(self, source: Source) -> list[str]:
        return [source.url]

    async def post_process_finding(
        self,
        finding: dict,
        extraction,
        source: Source,
    ) -> dict:
        """Boost confidence when high-impact competitor keywords are present."""
        text = f"{finding.get('summary', '')} {finding.get('content', '')}".lower()

        impact_matches = [kw for kw in HIGH_IMPACT_KEYWORDS if kw.lower() in text]
        if impact_matches:
            finding["confidence"] = min(finding.get("confidence", 0.5) + 0.1, 1.0)

        return finding
