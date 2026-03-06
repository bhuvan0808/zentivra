"""
Agent #2 - Foundation Model Provider Release Watcher.

Tracks model releases, API updates, pricing changes, and evaluation claims
from foundation model providers (OpenAI, Google, Anthropic, etc.).
"""

import re

from app.utils.logger import logger

from app.agents.base_agent import BaseAgent
from app.models.source import Source

# Keywords specific to model provider updates
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
    Agent #2: Foundation Model Provider Release Watcher.

    Tracks model releases, API updates, pricing changes, evaluation claims.
    Extracts structured model metadata: version, modalities, context length,
    tool use features, pricing, safety updates, benchmark claims.
    """

    @property
    def agent_type(self) -> str:
        return "model_provider"

    def _get_content_type(self) -> str:
        return "model provider changelog / API docs update"

    async def post_process_finding(
        self, finding: dict, extraction, source: Source
    ) -> dict:
        """
        Enrich model provider findings with structured metadata.

        Extracts:
        - Model version info
        - Context window sizes
        - Pricing info
        - API changes
        """
        text = f"{finding.get('title', '')} {finding.get('summary_long', '')}".lower()

        # Detect finding subcategory
        tags = finding.get("tags", [])

        has_model = any(kw.lower() in text for kw in MODEL_KEYWORDS)
        has_pricing = any(kw.lower() in text for kw in PRICING_KEYWORDS)
        has_api = any(kw.lower() in text for kw in API_KEYWORDS)

        if has_pricing:
            finding["category"] = "pricing"
            tags.append("pricing_change")
        elif has_model:
            finding["category"] = "models"
            tags.append("model_release")
        elif has_api:
            finding["category"] = "apis"
            tags.append("api_update")

        # Extract context window sizes (e.g., "128K context", "1M tokens")
        context_matches = re.findall(
            r"(\d+(?:\.\d+)?)\s*[KkMm]?\s*(?:context|token|ctx)",
            text,
        )
        if context_matches:
            tags.append("context_window")

        # Extract model names from text
        entities = finding.get("entities", {})
        models = entities.get("models", [])

        # Common model name patterns
        model_patterns = [
            r"GPT-\d+(?:\.\d+)?(?:-(?:turbo|mini|o|pro))?",
            r"Claude\s*\d+(?:\.\d+)?(?:\s*(?:Haiku|Sonnet|Opus))?",
            r"Gemini\s*(?:\d+(?:\.\d+)?)?(?:\s*(?:Pro|Ultra|Flash|Nano))?",
            r"Llama\s*\d+(?:\.\d+)?",
            r"Mistral\s*(?:Large|Medium|Small|Nemo)?",
            r"Command\s*R(?:\+)?",
        ]
        for pattern in model_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            models.extend(matches)

        models = list(set(models))
        entities["models"] = models
        finding["entities"] = entities
        finding["tags"] = list(set(tags))
        finding["publisher"] = source.name

        return finding
