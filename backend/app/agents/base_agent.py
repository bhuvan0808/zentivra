"""
Base Agent - Shared interface that all agent workers implement.

Provides the common pipeline: fetch → extract → detect changes → summarize → store.
Each agent subclass customizes source discovery and extraction logic.
"""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.change_detector import ChangeDetector
from app.core.extractor import Extractor
from app.core.fetcher import Fetcher, FetchResult
from app.core.summarizer import Summarizer, SummaryResult
from app.models.extraction import Extraction
from app.models.finding import Finding
from app.models.snapshot import Snapshot
from app.models.source import Source

logger = structlog.get_logger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all agent workers.

    Subclasses implement:
        - agent_type: str property identifying this agent
        - discover_urls(): find URLs to crawl from a source config
        - post_process_finding(): agent-specific enrichment
    """

    def __init__(self):
        self.fetcher = Fetcher()
        self.extractor = Extractor()
        self.change_detector = ChangeDetector()
        self.summarizer = Summarizer()

    @property
    @abstractmethod
    def agent_type(self) -> str:
        """Agent type identifier (e.g., 'competitor', 'model_provider')."""
        ...

    @property
    def agent_name(self) -> str:
        """Human-readable agent name."""
        return self.agent_type.replace("_", " ").title()

    async def run(
        self,
        run_id: str,
        sources: list[Source],
        since: Optional[datetime] = None,
        db: Optional[AsyncSession] = None,
    ) -> list[dict]:
        """
        Execute the agent pipeline for all assigned sources.

        Pipeline per source:
        1. Discover URLs (RSS/sitemap/direct)
        2. Fetch each URL
        3. Extract text + metadata
        4. Detect content changes
        5. Summarize new/changed content via LLM
        6. Store snapshots, extractions, and findings

        Args:
            run_id: Current pipeline run ID
            sources: List of Source objects assigned to this agent
            since: Only process content newer than this timestamp
            db: Database session for persistence

        Returns:
            List of finding dicts ready for dedup/ranking
        """
        all_findings = []
        agent_log = {
            "sources_processed": 0,
            "urls_fetched": 0,
            "findings_created": 0,
            "errors": [],
        }

        logger.info(
            "agent_run_start",
            agent=self.agent_type,
            run_id=run_id[:8],
            sources=len(sources),
        )

        for source in sources:
            if not source.enabled:
                continue

            try:
                findings = await self._process_source(run_id, source, since, db)
                all_findings.extend(findings)
                agent_log["sources_processed"] += 1
                agent_log["findings_created"] += len(findings)

            except Exception as e:
                error_msg = f"Error processing source '{source.name}': {e}"
                logger.error("agent_source_error", source=source.name, error=str(e))
                agent_log["errors"].append(error_msg)

        logger.info(
            "agent_run_complete",
            agent=self.agent_type,
            findings=len(all_findings),
            **agent_log,
        )

        return all_findings

    async def _process_source(
        self,
        run_id: str,
        source: Source,
        since: Optional[datetime],
        db: Optional[AsyncSession],
    ) -> list[dict]:
        """Process a single source: discover → fetch → extract → summarize."""
        findings = []

        # Step 1: Discover URLs to crawl
        urls = await self.discover_urls(source)
        logger.info(
            "urls_discovered",
            agent=self.agent_type,
            source=source.name,
            urls=len(urls),
        )

        if not urls:
            return findings

        # Step 2-5: Process each URL
        for url in urls:
            try:
                finding = await self._process_url(run_id, source, url, since, db)
                if finding:
                    findings.append(finding)
            except Exception as e:
                logger.error(
                    "url_processing_error",
                    url=url,
                    source=source.name,
                    error=str(e),
                )

        return findings

    async def _process_url(
        self,
        run_id: str,
        source: Source,
        url: str,
        since: Optional[datetime],
        db: Optional[AsyncSession],
    ) -> Optional[dict]:
        """Process a single URL through the pipeline."""

        # Step 2: Fetch
        fetch_result = await self.fetcher.fetch(
            url,
            rate_limit_rpm=source.rate_limit_rpm,
        )

        if not fetch_result.success:
            logger.warning("fetch_failed", url=url, error=fetch_result.error)
            return None

        # Step 3: Extract text + metadata
        extraction = self.extractor.extract_html(
            fetch_result.content,
            url=url,
            css_selectors=source.css_selectors,
        )

        if not extraction.success or not extraction.text:
            logger.warning("extraction_failed", url=url, error=extraction.error)
            return None

        # Step 4: Detect changes
        previous_content = None
        if db:
            previous_content = await self._get_previous_content(source.id, url, db)

        change = self.change_detector.compare(previous_content, extraction.text)

        # Skip if content hasn't significantly changed
        if not self.change_detector.is_significant_change(change):
            logger.debug("no_significant_change", url=url)
            # Still save snapshot for tracking
            if db:
                await self._save_snapshot(
                    run_id, source.id, url, fetch_result, extraction,
                    content_changed=False, db=db,
                )
            return None

        # Step 5: Summarize via LLM
        summary = await self.summarizer.summarize(
            content=extraction.text,
            source_name=source.name,
            source_url=url,
            content_type=self._get_content_type(),
        )

        if not summary.success:
            logger.warning("summarization_failed", url=url, error=summary.error)
            return None

        # Step 6: Store in database
        if db:
            await self._save_snapshot(
                run_id, source.id, url, fetch_result, extraction,
                content_changed=True, db=db,
            )

        # Build finding dict
        finding = {
            "id": str(uuid.uuid4()),
            "run_id": run_id,
            "source_id": source.id,
            "title": summary.title or extraction.title or "Untitled",
            "date_detected": datetime.now(timezone.utc).isoformat(),
            "source_url": url,
            "publisher": source.name,
            "category": summary.category,
            "summary_short": summary.summary_short,
            "summary_long": summary.summary_long,
            "why_it_matters": summary.why_it_matters,
            "evidence": summary.evidence,
            "confidence": summary.confidence,
            "tags": summary.tags,
            "entities": summary.entities,
            "diff_hash": change.current_hash,
            "impact_score": 0.0,  # Will be set by Ranker
            "is_duplicate": False,  # Will be set by Dedup
            "cluster_id": None,
        }

        # Agent-specific enrichment
        finding = await self.post_process_finding(finding, extraction, source)

        logger.info(
            "finding_created",
            title=finding["title"][:60],
            confidence=finding["confidence"],
            category=finding["category"],
        )

        return finding

    async def discover_urls(self, source: Source) -> list[str]:
        """
        Discover URLs to crawl from a source.

        Default strategy: RSS feed → direct URL.
        Subclasses can override for custom discovery (sitemap, API, etc.).
        """
        urls = []

        # Try RSS/Atom feed first
        if source.feed_url:
            feed_urls = await self._discover_from_feed(source.feed_url)
            urls.extend(feed_urls)

        # If no feed entries, use the direct URL
        if not urls:
            urls.append(source.url)

        return urls

    async def _discover_from_feed(self, feed_url: str) -> list[str]:
        """Fetch and parse an RSS/Atom feed to discover article URLs."""
        result = await self.fetcher.fetch(feed_url, use_playwright_fallback=False)
        if not result.success:
            return []

        entries = self.extractor.extract_feed(result.content, feed_url)

        # Return up to 10 most recent entry URLs
        return [e.link for e in entries[:10] if e.link]

    async def post_process_finding(
        self, finding: dict, extraction, source: Source
    ) -> dict:
        """
        Agent-specific post-processing of a finding.

        Override in subclasses to add custom fields, adjust confidence, etc.
        """
        return finding

    def _get_content_type(self) -> str:
        """Return the content type label for this agent."""
        return "web page"

    async def _get_previous_content(
        self, source_id: str, url: str, db: AsyncSession
    ) -> Optional[str]:
        """Get the most recent extracted content for a URL from a previous run."""
        try:
            result = await db.execute(
                select(Extraction.extracted_text)
                .join(Snapshot, Extraction.snapshot_id == Snapshot.id)
                .where(Snapshot.source_id == source_id)
                .where(Snapshot.url == url)
                .where(Snapshot.content_changed == True)
                .order_by(Snapshot.fetched_at.desc())
                .limit(1)
            )
            row = result.scalar_one_or_none()
            return row
        except Exception as e:
            logger.error("previous_content_error", url=url, error=str(e))
            return None

    async def _save_snapshot(
        self,
        run_id: str,
        source_id: str,
        url: str,
        fetch_result: FetchResult,
        extraction,
        content_changed: bool,
        db: AsyncSession,
    ):
        """Save snapshot and extraction to database."""
        try:
            snapshot = Snapshot(
                source_id=source_id,
                run_id=run_id,
                url=url,
                content_hash=fetch_result.content_hash,
                raw_content=fetch_result.content[:50000],  # Cap at 50KB
                http_status=fetch_result.status_code,
                content_changed=content_changed,
            )
            db.add(snapshot)
            await db.flush()

            ext = Extraction(
                snapshot_id=snapshot.id,
                extracted_text=extraction.text[:30000],  # Cap at 30KB
                metadata_={
                    "title": extraction.title,
                    "author": extraction.author,
                    "method": extraction.method,
                },
                extraction_method=extraction.method,
            )
            db.add(ext)
            await db.flush()

        except Exception as e:
            logger.error("save_snapshot_error", url=url, error=str(e))

    async def close(self):
        """Cleanup resources."""
        await self.fetcher.close()
