"""
Agent #4 - HuggingFace Benchmark Tracker.

Tracks HuggingFace leaderboards, trending models, evaluation datasets,
and new SOTA claims.
"""

import re
from typing import Optional

import structlog

from app.agents.base_agent import BaseAgent
from app.models.source import Source

logger = structlog.get_logger(__name__)

# Major benchmark names to track
BENCHMARK_NAMES = [
    "MMLU", "ARC", "HellaSwag", "TruthfulQA", "GSM8K", "WinoGrande",
    "HumanEval", "MBPP", "MATH", "BigBench", "IFEval",
    "MT-Bench", "AlpacaEval", "Chatbot Arena", "ELO",
    "GPQA", "MuSR", "BBH",
]

# Model families to track
MODEL_FAMILIES = [
    "Llama", "Mistral", "Mixtral", "Falcon", "Phi",
    "Qwen", "Yi", "DeepSeek", "Gemma", "Command",
    "DBRX", "Grok", "Jamba", "InternLM", "Baichuan",
    "StarCoder", "CodeLlama", "WizardLM", "Vicuna",
    "Orca", "Zephyr", "OpenHermes", "Neural",
]


class HFBenchmarkTracker(BaseAgent):
    """
    Agent #4: HuggingFace Benchmark Tracker.

    Tracks:
    - HF leaderboard movements
    - Trending models
    - Evaluation datasets
    - New SOTA claims

    Outputs:
    - Leaderboard movements
    - Task improvements
    - Model family trends
    - Reproducibility notes
    """

    @property
    def agent_type(self) -> str:
        return "hf_benchmark"

    def _get_content_type(self) -> str:
        return "benchmark leaderboard / model evaluation results"

    async def discover_urls(self, source: Source) -> list[str]:
        """
        Discover URLs for HF benchmark tracking.

        For leaderboards: direct URL (JS-heavy, may need Playwright).
        For trending: HF API or direct page.
        """
        urls = []

        if "huggingface" in source.url:
            # For HF pages, we may also want API endpoints
            urls.append(source.url)

            # Add HF API endpoint for trending models
            if "models" in source.url and "sort=trending" in source.url:
                urls.append(
                    "https://huggingface.co/api/models?sort=trending&limit=20"
                )

        elif source.feed_url:
            feed_urls = await self._discover_from_feed(source.feed_url)
            urls.extend(feed_urls)

        else:
            urls.append(source.url)

        return urls[:5]  # Cap for HF sources

    async def post_process_finding(
        self, finding: dict, extraction, source: Source
    ) -> dict:
        """
        Enrich benchmark findings with:
        - Benchmark-specific category
        - Model family detection
        - Benchmark names detection
        - SOTA claim flagging
        """
        finding["category"] = "benchmarks"
        finding["publisher"] = source.name

        text = f"{finding.get('title', '')} {finding.get('summary_long', '')}".lower()
        tags = finding.get("tags", [])

        # Detect mentioned benchmarks
        mentioned_benchmarks = []
        for bench in BENCHMARK_NAMES:
            if bench.lower() in text:
                mentioned_benchmarks.append(bench)

        if mentioned_benchmarks:
            tags.extend(mentioned_benchmarks)
            tags.append("benchmark_result")

        # Detect model families
        entities = finding.get("entities", {})
        models = entities.get("models", [])

        for family in MODEL_FAMILIES:
            if family.lower() in text:
                # Try to find the specific model name (e.g., "Llama-3.1-70B")
                pattern = rf"{family}[\s\-]*\d*(?:\.\d+)?(?:\s*[-]?\s*\d+[BbMm])?"
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    models.extend(matches)
                else:
                    models.append(family)

        models = list(set(models))
        entities["models"] = models
        entities["benchmarks"] = mentioned_benchmarks
        finding["entities"] = entities

        # Flag SOTA claims
        sota_patterns = [
            r"state[\s-]of[\s-]the[\s-]art",
            r"\bSOTA\b",
            r"surpass",
            r"outperform",
            r"new record",
            r"#1",
            r"first place",
            r"top[\s-]?1\b",
            r"beats? (?:GPT|Claude|Gemini|Llama)",
        ]
        is_sota = any(re.search(p, text, re.IGNORECASE) for p in sota_patterns)

        if is_sota:
            tags.append("sota_claim")
            finding["confidence"] = min(finding["confidence"] + 0.05, 1.0)

        # Flag trending models
        if "trending" in source.url.lower() or "trending" in text:
            tags.append("trending")

        finding["tags"] = list(set(tags))

        return finding
