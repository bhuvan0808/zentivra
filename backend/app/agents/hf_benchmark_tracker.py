"""
Agent #4 - HuggingFace Benchmark Tracker.

Tracks HuggingFace leaderboards, trending models, evaluation datasets,
and new SOTA claims.
"""

import re

from app.agents.base_agent import BaseAgent
from app.models.source import Source

SOTA_PATTERNS = [
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


class HFBenchmarkTracker(BaseAgent):

    @property
    def agent_type(self) -> str:
        return "hf_benchmark"

    def _get_content_type(self) -> str:
        return "benchmark leaderboard / model evaluation results"

    async def discover_urls(self, source: Source) -> list[str]:
        urls = [source.url]

        if "huggingface" in source.url:
            if "models" in source.url and "sort=trending" in source.url:
                urls.append("https://huggingface.co/api/models?sort=trending&limit=20")

        return urls[:5]

    async def post_process_finding(
        self, finding: dict, extraction, source: Source,
    ) -> dict:
        finding["category"] = "benchmarks"

        text = f"{finding.get('summary', '')} {finding.get('content', '')}".lower()

        is_sota = any(re.search(p, text, re.IGNORECASE) for p in SOTA_PATTERNS)
        if is_sota:
            finding["confidence"] = min(finding.get("confidence", 0.5) + 0.05, 1.0)

        return finding
