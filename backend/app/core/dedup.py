"""
Deduplication Engine - Detect and cluster duplicate/similar findings.

Uses sentence-transformers for semantic similarity and
agglomerative clustering for topic grouping.
"""

import hashlib
from dataclasses import dataclass, field
from typing import Optional

from app.utils.logger import logger
from app.config import settings

@dataclass
class DedupResult:
    """Result of deduplication for a set of findings."""
    unique_findings: list[dict] = field(default_factory=list)
    duplicate_ids: list[str] = field(default_factory=list)
    clusters: dict[str, list[str]] = field(default_factory=dict)  # cluster_id -> finding_ids
    total_input: int = 0
    total_unique: int = 0
    total_duplicates: int = 0


class DedupEngine:
    """
    Deduplication and clustering engine for findings.

    Uses two strategies:
    1. Exact hash matching (fast, catches identical content)
    2. Semantic similarity via embeddings (catches near-duplicates)

    Usage:
        engine = DedupEngine()
        result = engine.deduplicate(findings)
    """

    def __init__(
        self,
        similarity_threshold: float = 0.85,
        use_semantic_dedup: Optional[bool] = None,
    ):
        self.similarity_threshold = similarity_threshold
        self.use_semantic_dedup = (
            settings.enable_semantic_dedup
            if use_semantic_dedup is None
            else use_semantic_dedup
        )
        self._model = None

    def _get_embedding_model(self):
        """Lazy-load the sentence transformer model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("embedding_model_loaded model=all-MiniLM-L6-v2")
            except ImportError:
                logger.warning("sentence_transformers_not_installed")
                return None
        return self._model

    def _compute_text_hash(self, text: str) -> str:
        """Compute hash for exact dedup."""
        normalized = " ".join(text.lower().split())
        return hashlib.md5(normalized.encode()).hexdigest()

    def deduplicate(self, findings: list[dict]) -> DedupResult:
        """
        Deduplicate a list of findings.

        Args:
            findings: List of finding dicts, each must have 'id', 'title', 'summary_short'

        Returns:
            DedupResult with unique findings, duplicate IDs, and cluster assignments
        """
        if not findings:
            return DedupResult()

        total = len(findings)
        logger.info("dedup_start total_findings=%d", total)

        # Phase 1: Exact hash dedup
        seen_hashes = {}
        duplicate_ids = set()

        for f in findings:
            text = f"{f.get('title', '')} {f.get('summary_short', '')}"
            text_hash = self._compute_text_hash(text)

            if text_hash in seen_hashes:
                duplicate_ids.add(f["id"])
                logger.debug("exact_duplicate finding_id=%s", f["id"])
            else:
                seen_hashes[text_hash] = f["id"]

        # Phase 2: Semantic similarity dedup
        non_dup_findings = [f for f in findings if f["id"] not in duplicate_ids]

        if self.use_semantic_dedup and len(non_dup_findings) > 1:
            model = self._get_embedding_model()
            if model:
                semantic_dups = self._semantic_dedup(non_dup_findings, model)
                duplicate_ids.update(semantic_dups)

        # Phase 3: Cluster remaining unique findings by topic
        unique_findings = [f for f in findings if f["id"] not in duplicate_ids]
        clusters = self._cluster_findings(unique_findings)

        # Mark duplicates in the original findings
        for f in findings:
            f["is_duplicate"] = f["id"] in duplicate_ids
            f["cluster_id"] = None
            for cluster_id, member_ids in clusters.items():
                if f["id"] in member_ids:
                    f["cluster_id"] = cluster_id
                    break

        result = DedupResult(
            unique_findings=unique_findings,
            duplicate_ids=list(duplicate_ids),
            clusters=clusters,
            total_input=total,
            total_unique=len(unique_findings),
            total_duplicates=len(duplicate_ids),
        )

        logger.info(
            "dedup_complete total=%d unique=%d duplicates=%d clusters=%d",
            total,
            result.total_unique,
            result.total_duplicates,
            len(clusters),
        )

        return result

    def _semantic_dedup(
        self, findings: list[dict], model
    ) -> set[str]:
        """Use embeddings to find semantically similar findings."""
        import numpy as np

        texts = [
            f"{f.get('title', '')}. {f.get('summary_short', '')}"
            for f in findings
        ]

        try:
            embeddings = model.encode(texts, show_progress_bar=False)

            # Compute cosine similarity matrix
            from sklearn.metrics.pairwise import cosine_similarity
            sim_matrix = cosine_similarity(embeddings)

            duplicate_ids = set()
            n = len(findings)

            for i in range(n):
                if findings[i]["id"] in duplicate_ids:
                    continue
                for j in range(i + 1, n):
                    if findings[j]["id"] in duplicate_ids:
                        continue
                    if sim_matrix[i][j] >= self.similarity_threshold:
                        # Keep the one with higher confidence
                        conf_i = findings[i].get("confidence", 0)
                        conf_j = findings[j].get("confidence", 0)
                        if conf_i >= conf_j:
                            duplicate_ids.add(findings[j]["id"])
                        else:
                            duplicate_ids.add(findings[i]["id"])

                        logger.debug(
                            "semantic_duplicate similarity=%.3f kept=%s",
                            float(sim_matrix[i][j]),
                            findings[i]["id"] if conf_i >= conf_j else findings[j]["id"],
                        )

            return duplicate_ids

        except Exception as e:
            logger.error("semantic_dedup_error error=%s", str(e))
            return set()

    def _cluster_findings(self, findings: list[dict]) -> dict[str, list[str]]:
        """
        Cluster findings by topic using their categories.

        Categories from spec: Models, APIs, Pricing, Benchmarks, Safety, Tooling
        """
        clusters = {}

        for f in findings:
            category = f.get("category", "other")
            cluster_id = f"cluster_{category}"

            if cluster_id not in clusters:
                clusters[cluster_id] = []
            clusters[cluster_id].append(f["id"])

        return clusters
