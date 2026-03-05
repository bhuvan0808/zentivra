"""
Digest Compiler - Aggregates findings into a daily intelligence digest.

Steps:
1. Deduplicate findings
2. Cluster by topic and entity
3. Rank by impact
4. Generate narrative per section
5. Create executive summary
6. Hand off to PDF renderer and email service
"""

from datetime import date, datetime, timezone
from typing import Optional

from app.utils.logger import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings, DIGESTS_DIR
from app.core.dedup import DedupEngine
from app.core.ranker import Ranker
from app.core.summarizer import Summarizer
from app.models.digest import Digest
from app.models.finding import Finding
from app.models.run import Run

from app.utils.logger import logger

# Section ordering for the digest
SECTION_ORDER = [
    ("Competitor Releases", "competitor"),
    ("Model Provider Updates", "model_provider"),
    ("Research Publications", "research"),
    ("HuggingFace Benchmarks", "hf_benchmark"),
]

# Category display names
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
    Compiles all findings from a run into a structured daily digest.

    Usage:
        compiler = DigestCompiler()
        digest = await compiler.compile(run_id, findings, db)
    """

    def __init__(self):
        self.dedup_engine = DedupEngine()
        self.ranker = Ranker(use_llm=True)
        self.summarizer = Summarizer()

    async def compile(
        self,
        run_id: str,
        findings: list[dict],
        db: Optional[AsyncSession] = None,
    ) -> dict:
        """
        Compile findings into a complete digest.

        Returns dict with:
        - executive_summary
        - sections (dict of section_name -> {narrative, findings})
        - total_findings
        -         pdf_path (after rendering)
        """
        logger.info("digest_compile_start run_id=%s findings=%d", run_id[:8], len(findings))

        if not findings:
            return self._empty_digest(run_id)

        # Step 1: Deduplicate
        dedup_result = self.dedup_engine.deduplicate(findings)
        unique_findings = dedup_result.unique_findings
        logger.info(
            "dedup_complete unique=%d duplicates=%d",
            dedup_result.total_unique,
            dedup_result.total_duplicates,
        )

        # Step 2: Rank by impact
        ranked_findings = await self.ranker.rank_findings(unique_findings)

        # Step 3: Organize by section (agent type)
        sections = self._organize_by_section(ranked_findings)

        # Step 4: Generate narratives
        narratives = {}
        try:
            findings_for_narrative = {
                section_name: section_data["findings"]
                for section_name, section_data in sections.items()
            }
            narratives = await self.summarizer.generate_narrative(findings_for_narrative)
        except Exception as e:
            logger.error("narrative_generation_error error=%s", str(e))
            for section_name in sections:
                narratives[section_name] = self._fallback_narrative(
                    sections[section_name]["findings"]
                )

        # Add narratives to sections
        for section_name, narrative in narratives.items():
            if section_name in sections:
                sections[section_name]["narrative"] = narrative

        # Step 5: Generate executive summary
        executive_summary = ""
        try:
            executive_summary = await self.summarizer.generate_executive_summary(
                narratives, len(ranked_findings)
            )
        except Exception as e:
            logger.error("executive_summary_error error=%s", str(e))
            executive_summary = self._fallback_executive_summary(
                ranked_findings, sections
            )

        # Step 6: Save findings to DB
        if db:
            await self._save_findings(ranked_findings, db)

        digest_data = {
            "run_id": run_id,
            "date": date.today(),
            "executive_summary": executive_summary,
            "sections": sections,
            "total_findings": len(ranked_findings),
            "total_duplicates_removed": dedup_result.total_duplicates,
            "narratives": narratives,
        }

        logger.info(
            "digest_compile_complete sections=%d total_findings=%d",
            len(sections),
            len(ranked_findings),
        )

        return digest_data

    def _organize_by_section(self, findings: list[dict]) -> dict:
        """Organize findings by agent type / section."""
        sections = {}

        # Group by agent source type
        agent_findings = {}
        for f in findings:
            agent_type = self._infer_agent_type(f)
            if agent_type not in agent_findings:
                agent_findings[agent_type] = []
            agent_findings[agent_type].append(f)

        # Map to section names in order
        for section_name, agent_type in SECTION_ORDER:
            section_findings = agent_findings.get(agent_type, [])
            if section_findings:
                # Also sub-group by category within section
                by_category = {}
                for f in section_findings:
                    cat = f.get("category", "other")
                    cat_name = CATEGORY_NAMES.get(cat, cat.title())
                    if cat_name not in by_category:
                        by_category[cat_name] = []
                    by_category[cat_name].append(f)

                sections[section_name] = {
                    "findings": section_findings,
                    "count": len(section_findings),
                    "by_category": by_category,
                    "narrative": "",
                }

        return sections

    def _infer_agent_type(self, finding: dict) -> str:
        """Infer agent type from finding tags/category."""
        tags = finding.get("tags", [])
        category = finding.get("category", "other")

        if "research_paper" in tags:
            return "research"
        if "benchmark_result" in tags or "sota_claim" in tags:
            return "hf_benchmark"
        if category in ("models", "apis", "pricing"):
            # Check if it's a competitor or model provider
            if any(t in tags for t in ["model_release", "api_update", "pricing_change"]):
                return "model_provider"
            return "competitor"
        if category == "benchmarks":
            return "hf_benchmark"
        if category == "research":
            return "research"

        return "competitor"  # Default

    def _fallback_narrative(self, findings: list[dict]) -> str:
        """Generate a simple bullet-point narrative when LLM is unavailable."""
        if not findings:
            return "No significant updates in this area today."

        lines = [f"**{len(findings)} updates detected:**\n"]
        for f in findings[:10]:
            title = f.get("title", "Untitled")
            summary = f.get("summary_short", "")
            confidence = f.get("confidence", 0)
            lines.append(f"- **{title}** (confidence: {confidence:.0%})")
            if summary:
                lines.append(f"  {summary}")

        return "\n".join(lines)

    def _fallback_executive_summary(
        self, findings: list[dict], sections: dict
    ) -> str:
        """Generate a basic executive summary when LLM is unavailable."""
        total = len(findings)
        section_counts = {name: data["count"] for name, data in sections.items()}

        summary_parts = [f"Today's AI Radar detected **{total} findings** across the AI landscape.\n"]

        for name, count in section_counts.items():
            summary_parts.append(f"- **{name}**: {count} updates")

        if findings:
            top = findings[0]
            summary_parts.append(
                f"\n**Top finding**: {top.get('title', 'N/A')} "
                f"(impact: {top.get('impact_score', 0):.2f})"
            )

        return "\n".join(summary_parts)

    def _empty_digest(self, run_id: str) -> dict:
        """Return an empty digest structure."""
        return {
            "run_id": run_id,
            "date": date.today(),
            "executive_summary": "No significant AI developments detected today.",
            "sections": {},
            "total_findings": 0,
            "total_duplicates_removed": 0,
            "narratives": {},
        }

    async def _save_findings(self, findings: list[dict], db: AsyncSession):
        """Persist scored findings to the database."""
        try:
            for f in findings:
                finding = Finding(
                    id=f["id"],
                    run_id=f["run_id"],
                    source_id=f["source_id"],
                    title=f.get("title", "Untitled"),
                    source_url=f.get("source_url", ""),
                    publisher=f.get("publisher"),
                    category=f.get("category", "other"),
                    summary_short=f.get("summary_short"),
                    summary_long=f.get("summary_long"),
                    why_it_matters=f.get("why_it_matters"),
                    evidence=f.get("evidence"),
                    confidence=f.get("confidence", 0.5),
                    tags=f.get("tags"),
                    entities=f.get("entities"),
                    diff_hash=f.get("diff_hash"),
                    impact_score=f.get("impact_score", 0.0),
                    relevance_score=f.get("relevance_score", 0.0),
                    novelty_score=f.get("novelty_score", 0.0),
                    credibility_score=f.get("credibility_score", 0.0),
                    actionability_score=f.get("actionability_score", 0.0),
                    is_duplicate=f.get("is_duplicate", False),
                    cluster_id=f.get("cluster_id"),
                )
                db.add(finding)

            await db.flush()
            logger.info("findings_saved count=%d", len(findings))

        except Exception as e:
            logger.error("save_findings_error error=%s", str(e))
