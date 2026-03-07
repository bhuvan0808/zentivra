"""
Base Agent - Shared interface for all agent workers.

Pipeline per source URL:  fetch -> extract -> preprocess -> AI summarize
Returns a list of finding dicts; the orchestrator handles DB persistence.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Optional

from app.config import settings
from app.core.extractor import Extractor
from app.core.fetcher import Fetcher
from app.core.preprocessor import preprocess
from app.core.summarizer import Summarizer
from app.models.run import Run
from app.models.source import Source
from app.utils.logger import logger


class BaseAgent(ABC):
    """
    Abstract base class for agent workers.

    Subclasses implement:
        - agent_type: str property
        - discover_urls(): custom URL discovery from a Source
        - post_process_finding(): agent-specific enrichment
    """

    def __init__(self):
        self.fetcher = Fetcher()
        self.extractor = Extractor()
        self.summarizer = Summarizer()

    @property
    @abstractmethod
    def agent_type(self) -> str: ...

    @property
    def agent_name(self) -> str:
        return self.agent_type.replace("_", " ").title()

    async def run(
        self,
        sources: list[Source],
        run_config: Run | None = None,
        run_logger=None,
    ) -> dict:
        """Execute the agent pipeline for all assigned sources.

        Returns structured result dict:
            findings  - list of finding dicts
            errors    - list of human-readable error strings
            urls_attempted - total URLs the agent tried to process
            urls_succeeded - URLs that produced a finding
        """
        aggregate: dict = {
            "findings": [],
            "errors": [],
            "urls_attempted": 0,
            "urls_succeeded": 0,
        }

        logger.info(
            "agent_run_start agent=%s sources=%d",
            self.agent_type,
            len(sources),
        )
        if run_logger:
            run_logger.info(
                "agent_run_start",
                step="pipeline",
                sources=len(sources),
            )

        for source in sources:
            if not source.is_enabled:
                continue

            try:
                if run_logger:
                    run_logger.info(
                        "source_processing_start",
                        step="source_resolution",
                        source=source.display_name,
                        url=source.url,
                    )
                source_result = await self._process_source(
                    source,
                    run_config,
                    run_logger,
                )
                aggregate["findings"].extend(source_result["findings"])
                aggregate["errors"].extend(source_result["errors"])
                aggregate["urls_attempted"] += source_result["urls_attempted"]
                aggregate["urls_succeeded"] += source_result["urls_succeeded"]

                if run_logger:
                    run_logger.info(
                        "source_processing_complete",
                        step="source_resolution",
                        source=source.display_name,
                        findings=len(source_result["findings"]),
                        errors=len(source_result["errors"]),
                    )
            except Exception as exc:
                logger.error(
                    "agent_source_error agent=%s source=%s err=%s",
                    self.agent_type,
                    source.display_name,
                    str(exc)[:200],
                )
                if run_logger:
                    run_logger.error(
                        "source_processing_error",
                        step="source_resolution",
                        source=source.display_name,
                        error=str(exc)[:200],
                    )
                aggregate["errors"].append(
                    f"source:{source.display_name}: {str(exc)[:200]}"
                )

        logger.info(
            "agent_run_complete agent=%s findings=%d errors=%d attempted=%d succeeded=%d",
            self.agent_type,
            len(aggregate["findings"]),
            len(aggregate["errors"]),
            aggregate["urls_attempted"],
            aggregate["urls_succeeded"],
        )
        if run_logger:
            run_logger.info(
                "agent_run_complete",
                step="pipeline",
                findings=len(aggregate["findings"]),
                errors=len(aggregate["errors"]),
                urls_attempted=aggregate["urls_attempted"],
                urls_succeeded=aggregate["urls_succeeded"],
            )
        return aggregate

    async def _process_source(
        self,
        source: Source,
        run_config: Run | None,
        run_logger=None,
    ) -> dict:
        """Process a single source with BFS crawl up to configured crawl_depth.

        Returns a dict with findings, errors, urls_attempted, urls_succeeded.
        """
        result: dict = {
            "findings": [],
            "errors": [],
            "urls_attempted": 0,
            "urls_succeeded": 0,
        }
        crawl_depth = run_config.crawl_depth if run_config else 0

        seed_urls = await self.discover_urls(source)
        logger.info(
            "urls_discovered agent=%s source=%s count=%d depth=%d",
            self.agent_type,
            source.display_name,
            len(seed_urls),
            crawl_depth,
        )
        if run_logger:
            run_logger.info(
                "urls_discovered",
                step="fetch",
                source=source.display_name,
                count=len(seed_urls),
                crawl_depth=crawl_depth,
            )

        if not seed_urls:
            return result

        max_urls = max(1, int(settings.max_urls_per_source))
        source_timeout = max(0, int(settings.source_processing_timeout_seconds))
        url_timeout = max(1, int(settings.url_processing_timeout_seconds))
        source_start = asyncio.get_running_loop().time()

        visited: set[str] = set()
        current_level_urls = seed_urls[:max_urls]
        total_processed = 0

        for level in range(crawl_depth + 1):
            next_level_urls: list[str] = []

            for url in current_level_urls:
                if url in visited or total_processed >= max_urls:
                    continue

                if source_timeout:
                    elapsed = asyncio.get_running_loop().time() - source_start
                    if elapsed > source_timeout:
                        logger.warning(
                            "source_timeout agent=%s source=%s level=%d",
                            self.agent_type,
                            source.display_name,
                            level,
                        )
                        if run_logger:
                            run_logger.warning(
                                "source_timeout",
                                step="fetch",
                                source=source.display_name,
                                level=level,
                            )
                        result["errors"].append(f"source_timeout at level {level}")
                        return result

                visited.add(url)
                total_processed += 1
                result["urls_attempted"] += 1

                try:
                    finding, error_msg = await asyncio.wait_for(
                        self._process_url(source, url, run_config, run_logger),
                        timeout=url_timeout,
                    )
                    if finding:
                        result["findings"].append(finding)
                        result["urls_succeeded"] += 1
                        discovered = finding.pop("_discovered_links", [])
                        if level < crawl_depth and discovered:
                            next_level_urls.extend(
                                u for u in discovered if u not in visited
                            )
                    elif error_msg:
                        result["errors"].append(f"{url}: {error_msg}")
                except asyncio.TimeoutError:
                    logger.warning(
                        "url_timeout agent=%s url=%s timeout=%ds",
                        self.agent_type,
                        url,
                        url_timeout,
                    )
                    if run_logger:
                        run_logger.warning(
                            "url_timeout",
                            step="fetch",
                            url=url,
                            timeout_seconds=url_timeout,
                        )
                    result["errors"].append(f"{url}: timeout after {url_timeout}s")
                except Exception as exc:
                    logger.error(
                        "url_error agent=%s url=%s err=%s",
                        self.agent_type,
                        url,
                        str(exc)[:200],
                    )
                    if run_logger:
                        run_logger.error(
                            "url_error",
                            step="fetch",
                            url=url,
                            error=str(exc)[:200],
                        )
                    result["errors"].append(f"{url}: {str(exc)[:200]}")

            if not next_level_urls or level >= crawl_depth:
                break

            remaining = max_urls - total_processed
            current_level_urls = next_level_urls[:remaining]
            logger.info(
                "crawl_next_level agent=%s source=%s level=%d queued=%d",
                self.agent_type,
                source.display_name,
                level + 1,
                len(current_level_urls),
            )
            if run_logger:
                run_logger.info(
                    "crawl_next_level",
                    step="fetch",
                    source=source.display_name,
                    level=level + 1,
                    queued=len(current_level_urls),
                )

        return result

    async def _process_url(
        self,
        source: Source,
        url: str,
        run_config: Run | None,
        run_logger=None,
    ) -> tuple[Optional[dict], Optional[str]]:
        """Single URL pipeline: Fetch -> Extract -> Preprocess -> AI Summarize.

        Returns:
            (finding_dict, None)  on success
            (None, error_msg)     on failure
            (None, None)          on intentional skip (keyword filter)
        """

        # ── Fetch ──────────────────────────────────────────────
        if run_logger:
            run_logger.info("fetch_start", step="fetch", url=url[:120])
        fetch_result = await self.fetcher.fetch(url)

        if not fetch_result.success:
            logger.warning("fetch_failed url=%s err=%s", url, fetch_result.error)
            if run_logger:
                run_logger.warning(
                    "fetch_failed",
                    step="fetch",
                    url=url[:120],
                    error=str(fetch_result.error)[:200],
                )
            return None, f"fetch_failed: {fetch_result.error}"

        if run_logger:
            run_logger.info("fetch_done", step="fetch", url=url[:120])

        # ── Extract ────────────────────────────────────────────
        if run_logger:
            run_logger.info("extract_start", step="extract", url=url[:120])
        extraction = self.extractor.extract_html(
            fetch_result.content,
            url=url,
        )

        if not extraction.success or not extraction.text:
            logger.warning("extraction_failed url=%s", url)
            if run_logger:
                run_logger.warning(
                    "extract_failed",
                    step="extract",
                    url=url[:120],
                )
            return None, "extraction_failed: no usable text"

        if run_logger:
            run_logger.info(
                "extract_done",
                step="extract",
                url=url[:120],
                text_len=len(extraction.text),
            )

        # ── Preprocess ─────────────────────────────────────────
        if run_logger:
            run_logger.info("preprocess_start", step="preprocess", url=url[:120])
        cleaned_text = preprocess(extraction.text)
        if not cleaned_text:
            logger.warning("preprocess_empty url=%s", url)
            if run_logger:
                run_logger.warning(
                    "preprocess_empty",
                    step="preprocess",
                    url=url[:120],
                )
            return None, "preprocess_empty: no content after cleaning"

        if run_logger:
            run_logger.info(
                "preprocess_done",
                step="preprocess",
                url=url[:120],
                cleaned_len=len(cleaned_text),
            )

        # ── Keyword filter (intentional skip, not an error) ───
        if run_config and run_config.keywords:
            text_lower = cleaned_text.lower()
            if not any(kw.lower() in text_lower for kw in run_config.keywords):
                logger.info(
                    "keyword_filter_skip url=%s keywords=%s text_preview=%s",
                    url[:80],
                    run_config.keywords[:5],
                    cleaned_text[:150].replace("\n", " "),
                )
                if run_logger:
                    run_logger.info(
                        "keyword_filter_skip",
                        step="keyword_filter",
                        url=url[:120],
                    )
                return None, None

        # ── AI Summarize ───────────────────────────────────────
        if run_logger:
            run_logger.info("summarize_start", step="summarize", url=url[:120])
        summary = await self.summarizer.summarize(
            content=cleaned_text,
            source_name=source.display_name,
            source_url=url,
            content_type=self._get_content_type(),
        )

        if not summary.success:
            logger.warning("summarize_failed url=%s err=%s", url, summary.error)
            if run_logger:
                run_logger.warning(
                    "summarize_failed",
                    step="summarize",
                    url=url[:120],
                    error=str(summary.error)[:200],
                )
            return None, f"summarize_failed: {summary.error}"

        if run_logger:
            run_logger.info(
                "summarize_done",
                step="summarize",
                url=url[:120],
                category=summary.category,
            )

        # ── Build finding dict ─────────────────────────────────
        finding = {
            "content": cleaned_text[:5000],
            "summary": summary.summary_short or summary.summary_long or "",
            "src_url": url,
            "category": summary.category or "other",
            "confidence": summary.confidence or 0.5,
            "_discovered_links": getattr(extraction, "links", []),
        }

        finding = await self.post_process_finding(finding, extraction, source)

        logger.info(
            "finding_created agent=%s url=%s category=%s confidence=%.2f",
            self.agent_type,
            url[:60],
            finding["category"],
            finding["confidence"],
        )
        if run_logger:
            run_logger.info(
                "finding_created",
                step="summarize",
                url=url[:120],
                category=finding["category"],
                confidence=finding["confidence"],
            )
        return finding, None

    # ── Overridable hooks ──────────────────────────────────────────

    async def discover_urls(self, source: Source) -> list[str]:
        """Default URL discovery: just use source.url."""
        return [source.url]

    async def post_process_finding(
        self,
        finding: dict,
        extraction,
        source: Source,
    ) -> dict:
        """Agent-specific enrichment. Override in subclasses."""
        return finding

    def _get_content_type(self) -> str:
        return "web page"

    # ── Lifecycle ──────────────────────────────────────────────────

    async def close(self):
        """Release resources."""
        await self.fetcher.close()
