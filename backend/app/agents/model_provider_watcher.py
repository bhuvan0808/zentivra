"""
Agent #2 - Foundation Model Provider Release Watcher.

Domain focus: Tracks LLM provider announcements and model releases.
Produces findings from OpenAI, Google, Anthropic, and other foundation
model providers: model releases, API updates, pricing changes, changelogs.
"""

from app.agents.base_agent import BaseAgent
from app.models.source import Source

# Keywords for model-related content
MODEL_KEYWORDS = [
    "model",
    "context window",
    "context length",
    "token",
    "function calling",
    "tool use",
    "vision",
    "multimodal",
    "embedding",
    "fine-tuning",
    "fine tuning",
]

# Keywords for pricing-related content
PRICING_KEYWORDS = [
    "pricing",
    "cost",
    "price",
    "per token",
    "per million",
    "input tokens",
    "output tokens",
    "rate limit",
    "quota",
    "free tier",
    "credit",
]

# Keywords for API-related content
API_KEYWORDS = [
    "API",
    "endpoint",
    "SDK",
    "version",
    "deprecation",
    "breaking change",
    "migration",
    "changelog",
    "release",
]


class ModelProviderWatcher(BaseAgent):
    """
    Tracks LLM provider announcements and model releases.

    Specialization vs BaseAgent: Uses source.url directly (no custom URL
    discovery). Post-processes findings to set category (pricing, models,
    apis) based on keyword presence. Content type: "model provider changelog /
    API docs update".
    """

    @property
    def agent_type(self) -> str:
        return "model_provider"

    def _get_content_type(self) -> str:
        return "model provider changelog / API docs update"

    async def discover_urls(self, source: Source) -> list[str]:
        """Override: use source.url directly; no custom discovery."""
        return [source.url]

    async def post_process_finding(
        self,
        finding: dict,
        extraction,
        source: Source,
    ) -> dict:
        """Set category (pricing, models, apis) based on keyword presence."""
        text = f"{finding.get('summary', '')} {finding.get('content', '')}".lower()

        has_pricing = any(kw.lower() in text for kw in PRICING_KEYWORDS)
        has_model = any(kw.lower() in text for kw in MODEL_KEYWORDS)
        has_api = any(kw.lower() in text for kw in API_KEYWORDS)

        if has_pricing:
            finding["category"] = "pricing"
        elif has_model:
            finding["category"] = "models"
        elif has_api:
            finding["category"] = "apis"

        return finding
