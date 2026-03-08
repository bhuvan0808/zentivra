"""
Digest Compiler - Aggregates findings into a structured intelligence digest.

Steps:
1. Deduplicate findings
2. Rank by impact
3. Organize by agent type / section
4. Generate narrative per section (LLM)
5. Generate executive summary (LLM)

Returns a digest_data dict consumed by PDFRenderer.
Finding persistence is handled by the orchestrator, not the compiler.
"""

from datetime import date
from typing import Optional

from app.config import settings
from app.core.dedup import DedupEngine
from app.core.ranker import Ranker
from app.core.summarizer import Summarizer
from app.utils.logger import logger

# Section display order: (display name, agent_type key)
SECTION_ORDER = [
    ("Competitor Releases", "competitor"),
    ("Model Provider Updates", "model_provider"),
    ("Research Publications", "research"),
    ("HuggingFace Benchmarks", "hf_benchmark"),
]

# Maps internal category keys to human-readable section labels
CATEGORY_NAMES = {
    "models": "Model Releases",
    "apis": "API Updates",
    "pricing": "Pricing Changes",
    "benchmarks": "Benchmark Results",
    "safety": "Safety & Alignment",
    "tooling": "Developer Tooling",
    "research": "Research",
    "other": "Other Updates",
}


class DigestCompiler:
    """
    Compiles raw findings into a structured digest payload for PDF/HTML rendering.

    Responsibilities:
    - Deduplicate findings via similarity threshold
    - Rank findings by impact (LLM-assisted)
    - Organize by agent type and category
    - Generate section narratives and executive summary (LLM)
    - Fallback to template-based summaries on LLM errors
    """

    def __init__(
        self,
        similarity_threshold: float = 0.85,
        llm_provider: Optional[str] = None,
        llm_model: Optional[str] = None,
        ranking_weights: Optional[dict] = None,
    ):
        """
        Initialize the compiler with dedup, ranker, and summarizer.

        Args:
            similarity_threshold: Threshold for deduplication (0–1).
            llm_provider: Optional LLM provider override for ranking/summarization.
            llm_model: Optional model override.
            ranking_weights: Optional custom weights for the ranker.
        """
        self.dedup_engine = DedupEngine(similarity_threshold=similarity_threshold)
        self.ranker = Ranker(
            use_llm=True,
            llm_provider=llm_provider,
            llm_model=llm_model,
            weights=ranking_weights,
        )
        self.summarizer = Summarizer()

    async def compile(
        self,
        run_trigger_id: int,
        findings: list[dict],
    ) -> dict:
        """Compile finding dicts into a digest payload for the PDF renderer.

        Pipeline: deduplicate → rank → organize by section → generate narratives
        → generate executive summary → generate digest title. On LLM errors,
        falls back to template-based narratives/summaries.

        Args:
            run_trigger_id: Internal FK of the RunTrigger (for logging).
            findings: List of finding dicts from agents.

        Returns:
            dict with executive_summary, sections, total_findings, date,
            digest_title, narratives, total_duplicates_removed.
        """
        logger.info(
            "digest_compile_start run_trigger_id=%s findings=%d",
            run_trigger_id,
            len(findings),
        )

        if not findings:
            return self._empty_digest()

        # Step 1: Deduplicate
        dedup_result = self.dedup_engine.deduplicate(findings)
        unique_findings = dedup_result.unique_findings
        logger.info(
            "dedup_complete unique=%d duplicates=%d",
            dedup_result.total_unique,
            dedup_result.total_duplicates,
        )

        # Step 2: Rank
        ranked_findings = await self.ranker.rank_findings(unique_findings)

        # Step 3: Organize by section
        sections = self._organize_by_section(ranked_findings)

        # Step 4: Generate narratives
        narratives: dict[str, str] = {}
        try:
            findings_for_narrative = {
                name: data["findings"] for name, data in sections.items()
            }
            narratives = await self.summarizer.generate_narrative(
                findings_for_narrative
            )
        except Exception as exc:
            logger.error("narrative_generation_error err=%s", str(exc)[:200])
            for name in sections:
                narratives[name] = self._fallback_narrative(sections[name]["findings"])

        for name, narrative in narratives.items():
            if name in sections:
                sections[name]["narrative"] = narrative

        # Step 5: Executive summary
        executive_summary = ""
        try:
            executive_summary = await self.summarizer.generate_executive_summary(
                narratives,
                len(ranked_findings),
            )
        except Exception as exc:
            logger.error("executive_summary_error err=%s", str(exc)[:200])
            executive_summary = self._fallback_executive_summary(
                ranked_findings, sections
            )

        # Step 6: Generate content-based digest title
        digest_title = "AI Radar Digest"
        try:
            digest_title = await self.summarizer.generate_digest_title(ranked_findings)
        except Exception as exc:
            logger.error("digest_title_error err=%s", str(exc)[:200])

        digest_data = {
            "date": date.today(),
            "digest_title": digest_title,
            "executive_summary": executive_summary,
            "sections": sections,
            "total_findings": len(ranked_findings),
            "total_duplicates_removed": dedup_result.total_duplicates,
            "narratives": narratives,
        }

        logger.info(
            "digest_compile_complete sections=%d findings=%d",
            len(sections),
            len(ranked_findings),
        )
        return digest_data

    def _organize_by_section(self, findings: list[dict]) -> dict:
        """
        Group findings by agent type and category per SECTION_ORDER.

        Returns:
            dict mapping section names to {findings, count, by_category, narrative}.
        """
        agent_findings: dict[str, list[dict]] = {}
        for f in findings:
            agent_type = f.get("agent_type", "competitor")
            agent_findings.setdefault(agent_type, []).append(f)

        sections: dict[str, dict] = {}
        for section_name, agent_type in SECTION_ORDER:
            section_finds = agent_findings.get(agent_type, [])
            if section_finds:
                by_category: dict[str, list[dict]] = {}
                for f in section_finds:
                    cat = f.get("category", "other")
                    cat_name = CATEGORY_NAMES.get(cat, cat.title())
                    by_category.setdefault(cat_name, []).append(f)

                sections[section_name] = {
                    "findings": section_finds,
                    "count": len(section_finds),
                    "by_category": by_category,
                    "narrative": "",
                }

        return sections

    def _fallback_narrative(self, findings: list[dict]) -> str:
        """
        Generate a simple bullet-point narrative when LLM summarization fails.

        Returns a markdown-style list of up to 10 findings with summary and confidence.
        """
        if not findings:
            return "No significant updates in this area today."

        lines = [f"**{len(findings)} updates detected:**\n"]
        for f in findings[:10]:
            summary = f.get("summary", "")[:120]
            confidence = f.get("confidence", 0)
            lines.append(f"- {summary} (confidence: {confidence:.0%})")

        return "\n".join(lines)

    def _fallback_executive_summary(self, findings: list[dict], sections: dict) -> str:
        """
        Generate a simple executive summary when LLM generation fails.

        Returns markdown with total count and per-section counts.
        """
        total = len(findings)
        parts = [
            f"Today's AI Radar detected **{total} findings** across the AI landscape.\n"
        ]

        for name, data in sections.items():
            parts.append(f"- **{name}**: {data['count']} updates")

        return "\n".join(parts)

    def _empty_digest(self) -> dict:
        """Return a minimal digest payload when no findings are provided."""
        return {
            "date": date.today(),
            "executive_summary": "No significant AI developments detected today.",
            "sections": {},
            "total_findings": 0,
            "total_duplicates_removed": 0,
            "narratives": {},
        }
