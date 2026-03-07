"""
Agent #2 - Foundation Model Provider Release Watcher.

Tracks model releases, API updates, pricing changes from
foundation model providers (OpenAI, Google, Anthropic, etc.).
"""

from app.agents.base_agent import BaseAgent
from app.models.source import Source

MODEL_KEYWORDS = [
    "model", "context window", "context length", "token",
    "function calling", "tool use", "vision", "multimodal",
    "embedding", "fine-tuning", "fine tuning",
]

PRICING_KEYWORDS = [
    "pricing", "cost", "price", "per token", "per million",
    "input tokens", "output tokens", "rate limit", "quota",
    "free tier", "credit",
]

API_KEYWORDS = [
    "API", "endpoint", "SDK", "version", "deprecation",
    "breaking change", "migration", "changelog", "release",
]


class ModelProviderWatcher(BaseAgent):

    @property
    def agent_type(self) -> str:
        return "model_provider"

    def _get_content_type(self) -> str:
        return "model provider changelog / API docs update"

    async def discover_urls(self, source: Source) -> list[str]:
        return [source.url]

    async def post_process_finding(
        self, finding: dict, extraction, source: Source,
    ) -> dict:
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
