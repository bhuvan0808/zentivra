"""
Base Agent - Shared interface that all agent workers implement.

Provides the common pipeline: fetch -> extract -> detect changes -> summarize -> store.
Each agent subclass customizes source discovery and extraction logic.
"""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional

from app.utils.logger import logger
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
from app.utils.run_logger import RunLogger


class BaseAgent(ABC):
    """
    Abstract base class for all agent workers.

    Subclasses implement:
        - agent_type: str property identifying this agent
        - discover_urls(): find URLs to crawl from a source config
        - post_process_finding(): agent-specific enrichment
    """

    def __init__(
        self,
        llm_provider: Optional[str] = None,
        llm_model: Optional[str] = None,
    ):
        self.fetcher = Fetcher()
        self.extractor = Extractor()
        self.change_detector = ChangeDetector()
        self.summarizer = Summarizer(provider=llm_provider, model=llm_model)

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
        run_logger: Optional[RunLogger] = None,
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
        """
        rl = run_logger
        all_findings = []
        agent_log = {
            "sources_processed": 0,
            "urls_fetched": 0,
            "findings_created": 0,
            "errors": [],
        }

        if rl:
            rl.info(
                "agent_run_start",
                agent=self.agent_type,
                phase="init",
                sources=len(sources),
            )

        for source in sources:
            if not source.enabled:
                continue

            try:
                findings = await self._process_source(
                    run_id, source, since, db, rl
                )
                all_findings.extend(findings)
                agent_log["sources_processed"] += 1
                agent_log["findings_created"] += len(findings)

            except Exception as e:
                error_msg = f"Error processing source '{source.name}': {e}"
                if rl:
                    rl.error(
                        "agent_source_error",
                        agent=self.agent_type,
                        phase="error",
                        source=source.name,
                        error=str(e),
                    )
                else:
                    logger.error(
                        "agent_source_error source=%s error=%s",
                        source.name,
                        str(e),
                    )
                agent_log["errors"].append(error_msg)

        if rl:
            rl.info(
                "agent_run_complete",
                agent=self.agent_type,
                phase="done",
                findings=len(all_findings),
                sources_processed=agent_log["sources_processed"],
                urls_fetched=agent_log["urls_fetched"],
                findings_created=agent_log["findings_created"],
                error_count=len(agent_log["errors"]),
            )
        else:
            logger.info(
                "agent_run_complete agent=%s findings=%d",
                self.agent_type,
                len(all_findings),
            )

        return all_findings

    async def _process_source(
        self,
        run_id: str,
        source: Source,
        since: Optional[datetime],
        db: Optional[AsyncSession],
        rl: Optional[RunLogger] = None,
    ) -> list[dict]:
        """Process a single source: discover -> fetch -> extract -> summarize."""
        findings = []

        # Step 1: Discover URLs to crawl
        urls = await self.discover_urls(source)

        if rl:
            rl.info(
                "urls_discovered",
                agent=self.agent_type,
                phase="discover",
                source=source.name,
                url_count=len(urls),
            )

        if not urls:
            return findings

        # Step 2-5: Process each URL
        for idx, url in enumerate(urls, 1):
            try:
                finding = await self._process_url(
                    run_id, source, url, since, db, rl, url_idx=idx, url_total=len(urls)
                )
                if finding:
                    findings.append(finding)
            except Exception as e:
                if rl:
                    rl.error(
                        "url_processing_error",
                        agent=self.agent_type,
                        phase="error",
                        url=url,
                        source=source.name,
                        error=str(e),
                    )
                else:
                    logger.error(
                        "url_processing_error url=%s source=%s error=%s",
                        url,
                        source.name,
                        str(e),
                    )

        return findings

    async def _process_url(
        self,
        run_id: str,
        source: Source,
        url: str,
        since: Optional[datetime],
        db: Optional[AsyncSession],
        rl: Optional[RunLogger] = None,
        url_idx: int = 0,
        url_total: int = 0,
    ) -> Optional[dict]:
        """Process a single URL through the pipeline."""

        # Step 2: Fetch
        fetch_result = await self.fetcher.fetch(
            url,
            rate_limit_rpm=source.rate_limit_rpm,
        )

        if not fetch_result.success:
            if rl:
                rl.warning(
                    "fetch_failed",
                    agent=self.agent_type,
                    phase="fetch",
                    url=url,
                    status_code=fetch_result.status_code,
                    error=fetch_result.error,
                )
            else:
                logger.warning("fetch_failed url=%s error=%s", url, fetch_result.error)
            return None

        if rl:
            rl.info(
                "url_fetched",
                agent=self.agent_type,
                phase="fetch",
                url=url,
                status_code=fetch_result.status_code,
                content_length=len(fetch_result.content),
                method=fetch_result.method,
                progress=f"{url_idx}/{url_total}",
            )

        # Step 3: Extract text + metadata
        extraction = self.extractor.extract_html(
            fetch_result.content,
            url=url,
            css_selectors=source.css_selectors,
        )

        if not extraction.success or not extraction.text:
            if rl:
                rl.warning(
                    "extraction_failed",
                    agent=self.agent_type,
                    phase="extract",
                    url=url,
                    error=extraction.error,
                )
            else:
                logger.warning(
                    "extraction_failed url=%s error=%s", url, extraction.error
                )
            return None

        if rl:
            rl.info(
                "text_extracted",
                agent=self.agent_type,
                phase="extract",
                url=url,
                text_length=len(extraction.text),
                title=extraction.title,
                method=extraction.method,
            )

        # Step 4: Detect changes
        previous_content = None
        if db:
            previous_content = await self._get_previous_content(source.id, url, db)

        change = self.change_detector.compare(previous_content, extraction.text)

        if not self.change_detector.is_significant_change(change):
            if rl:
                rl.info(
                    "no_significant_change",
                    agent=self.agent_type,
                    phase="change_detect",
                    url=url,
                )
            if db:
                await self._save_snapshot(
                    run_id,
                    source.id,
                    url,
                    fetch_result,
                    extraction,
                    content_changed=False,
                    db=db,
                )
            return None

        if rl:
            rl.info(
                "change_detected",
                agent=self.agent_type,
                phase="change_detect",
                url=url,
                diff_hash=change.current_hash[:12],
            )

        # Step 5: Summarize via LLM
        if rl:
            rl.info(
                "summarization_start",
                agent=self.agent_type,
                phase="summarize",
                url=url,
            )

        summary = await self.summarizer.summarize(
            content=extraction.text,
            source_name=source.name,
            source_url=url,
            content_type=self._get_content_type(),
        )

        if not summary.success:
            if rl:
                rl.warning(
                    "summarization_failed",
                    agent=self.agent_type,
                    phase="summarize",
                    url=url,
                    error=summary.error,
                )
            else:
                logger.warning(
                    "summarization_failed url=%s error=%s", url, summary.error
                )
            return None

        if rl:
            rl.info(
                "summarization_complete",
                agent=self.agent_type,
                phase="summarize",
                url=url,
                confidence=summary.confidence,
                category=summary.category,
            )

        # Step 6: Store in database
        if db:
            await self._save_snapshot(
                run_id,
                source.id,
                url,
                fetch_result,
                extraction,
                content_changed=True,
                db=db,
            )

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
            "impact_score": 0.0,
            "is_duplicate": False,
            "cluster_id": None,
        }

        finding = await self.post_process_finding(finding, extraction, source)

        if rl:
            rl.info(
                "finding_created",
                agent=self.agent_type,
                phase="finding",
                title=finding["title"][:80],
                confidence=finding["confidence"],
                category=finding["category"],
                url=url,
            )

        return finding

    async def discover_urls(self, source: Source) -> list[str]:
        """
        Discover URLs to crawl from a source.

        Default strategy: RSS feed -> direct URL.
        Subclasses can override for custom discovery (sitemap, API, etc.).
        """
        urls = []

        if source.feed_url:
            feed_urls = await self._discover_from_feed(source.feed_url)
            urls.extend(feed_urls)

        if not urls:
            urls.append(source.url)

        return urls

    async def _discover_from_feed(self, feed_url: str) -> list[str]:
        """Fetch and parse an RSS/Atom feed to discover article URLs."""
        result = await self.fetcher.fetch(feed_url, use_playwright_fallback=False)
        if not result.success:
            return []

        entries = self.extractor.extract_feed(result.content, feed_url)
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
            logger.error("previous_content_error url=%s error=%s", url, str(e))
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
                raw_content=fetch_result.content[:50000],
                http_status=fetch_result.status_code,
                content_changed=content_changed,
            )
            db.add(snapshot)
            await db.flush()

            ext = Extraction(
                snapshot_id=snapshot.id,
                extracted_text=extraction.text[:30000],
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
            logger.error("save_snapshot_error url=%s error=%s", url, str(e))

    async def close(self):
        """Cleanup resources."""
        await self.fetcher.close()
