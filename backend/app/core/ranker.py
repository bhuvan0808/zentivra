"""
Ranker - Impact scoring for findings.

Uses the spec-defined formula:
  Impact = 0.35 * Relevance + 0.25 * Novelty + 0.20 * Credibility + 0.20 * Actionability

Scoring can be done via LLM-assisted evaluation or heuristic rules.
"""

import structlog

from app.core.summarizer import Summarizer

logger = structlog.get_logger(__name__)

# Weights from spec section 14
RELEVANCE_WEIGHT = 0.35
NOVELTY_WEIGHT = 0.25
CREDIBILITY_WEIGHT = 0.20
ACTIONABILITY_WEIGHT = 0.20


class Ranker:
    """
    Rank and score findings based on impact.

    Usage:
        ranker = Ranker()
        scored = await ranker.rank_findings(findings)
    """

    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm
        self._summarizer = Summarizer() if use_llm else None

    def compute_impact_score(
        self,
        relevance: float,
        novelty: float,
        credibility: float,
        actionability: float,
    ) -> float:
        """
        Compute impact score using the spec formula.

        All inputs should be on 0-10 scale.
        Returns score on 0-1 scale.
        """
        score = (
            RELEVANCE_WEIGHT * relevance
            + NOVELTY_WEIGHT * novelty
            + CREDIBILITY_WEIGHT * credibility
            + ACTIONABILITY_WEIGHT * actionability
        ) / 10.0

        return round(min(max(score, 0.0), 1.0), 3)

    async def rank_findings(self, findings: list[dict]) -> list[dict]:
        """
        Score and rank a list of findings.

        If LLM is available, uses LLM-assisted scoring.
        Otherwise, falls back to heuristic scoring.
        """
        for finding in findings:
            if self.use_llm and self._summarizer:
                try:
                    scores = await self._summarizer.rank(
                        title=finding.get("title", ""),
                        summary=finding.get("summary_short", ""),
                        category=finding.get("category", "other"),
                        source=finding.get("publisher", "Unknown"),
                    )
                    finding["relevance_score"] = scores.get("relevance", 5) / 10.0
                    finding["novelty_score"] = scores.get("novelty", 5) / 10.0
                    finding["credibility_score"] = scores.get("credibility", 5) / 10.0
                    finding["actionability_score"] = scores.get("actionability", 5) / 10.0
                    finding["impact_score"] = scores.get("impact_score", 0.5)

                except Exception as e:
                    logger.error("llm_ranking_error", error=str(e))
                    self._apply_heuristic_scores(finding)
            else:
                self._apply_heuristic_scores(finding)

        # Sort by impact score (descending)
        findings.sort(key=lambda f: f.get("impact_score", 0), reverse=True)

        logger.info(
            "ranking_complete",
            total=len(findings),
            top_score=findings[0].get("impact_score", 0) if findings else 0,
        )

        return findings

    def _apply_heuristic_scores(self, finding: dict):
        """
        Apply heuristic scoring based on category and confidence.
        Used as fallback when LLM is not available.
        """
        confidence = finding.get("confidence", 0.5)
        category = finding.get("category", "other")

        # Category-based relevance (higher for models and research)
        category_relevance = {
            "models": 8,
            "apis": 7,
            "pricing": 7,
            "benchmarks": 6,
            "safety": 7,
            "tooling": 5,
            "research": 7,
            "other": 4,
        }

        relevance = category_relevance.get(category, 5)
        novelty = 5  # Neutral default
        credibility = int(confidence * 10)
        actionability = 5

        # Boost for high-confidence findings
        if confidence >= 0.8:
            novelty += 1
            actionability += 1

        finding["relevance_score"] = relevance / 10.0
        finding["novelty_score"] = novelty / 10.0
        finding["credibility_score"] = credibility / 10.0
        finding["actionability_score"] = actionability / 10.0
        finding["impact_score"] = self.compute_impact_score(
            relevance, novelty, credibility, actionability
        )
