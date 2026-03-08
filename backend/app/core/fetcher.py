"""Fetcher layer — HTTP/RSS/Playwright URL fetching with retries.

First stage of the pipeline: fetch -> extract -> preprocess -> summarize -> dedup -> rank.

Primary: async httpx for fast HTTP fetching.
Fallback: Playwright for JavaScript-rendered pages (when content seems empty or bot-blocked).
Respects robots.txt, per-domain rate limiting, and exponential backoff on retries.
"""

import asyncio
import hashlib
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urljoin, urlparse

import httpx
from app.utils.logger import logger
from app.config import settings
from app.core.rate_limiter import rate_limiter

# User agent for requests
USER_AGENT = "Zentivra/1.0 (AI Research Intelligence Bot)"


@dataclass
class FetchResult:
    """Result of fetching a URL.

    Attributes:
        url: Requested URL.
        status_code: HTTP status code (0 if fetch failed before response).
        content: Raw response body (HTML, XML, etc.).
        content_hash: SHA256 hash of content (auto-computed if content present).
        content_type: Content-Type header value.
        error: Error message if success=False.
        success: True if fetch succeeded.
        method: "httpx" or "playwright".
        redirected_url: Final URL after redirects, or None if unchanged.
        headers: Response headers as dict.
    """

    url: str
    status_code: int
    content: str = ""
    content_hash: str = ""
    content_type: str = ""
    error: Optional[str] = None
    success: bool = True
    method: str = "httpx"  # httpx or playwright
    redirected_url: Optional[str] = None
    headers: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.content and not self.content_hash:
            self.content_hash = hashlib.sha256(self.content.encode("utf-8")).hexdigest()


class RobotsChecker:
    """Check robots.txt rules for URLs.

    Caches robots.txt per domain and parses Disallow rules to determine
    whether the user agent is allowed to fetch a given URL.
    """

    def __init__(self):
        self._cache: dict[str, Optional[str]] = {}
        self._lock = asyncio.Lock()

    async def is_allowed(self, url: str, client: httpx.AsyncClient) -> bool:
        """Check if we're allowed to fetch this URL per robots.txt."""
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        robots_url = f"{base_url}/robots.txt"

        async with self._lock:
            if base_url not in self._cache:
                try:
                    resp = await client.get(robots_url, timeout=10)
                    if resp.status_code == 200:
                        self._cache[base_url] = resp.text
                    else:
                        self._cache[base_url] = None  # No robots.txt = all allowed
                except Exception:
                    self._cache[base_url] = None

        robots_txt = self._cache.get(base_url)
        if robots_txt is None:
            return True

        # Simple robots.txt parsing — check for Disallow rules
        try:
            from robotexclusionrulesparser import RobotExclusionRulesParser

            parser = RobotExclusionRulesParser()
            parser.parse(robots_txt)
            return parser.is_allowed(USER_AGENT, url)
        except ImportError:
            # Fallback: basic check
            return self._basic_robots_check(robots_txt, url)

    def _basic_robots_check(self, robots_txt: str, url: str) -> bool:
        """Basic robots.txt check without external library.

        Parses User-agent and Disallow lines; returns False if path matches
        a Disallow rule for our agent.
        """
        parsed = urlparse(url)
        path = parsed.path

        in_our_section = False
        for line in robots_txt.split("\n"):
            line = line.strip()
            if line.lower().startswith("user-agent:"):
                agent = line.split(":", 1)[1].strip()
                in_our_section = agent == "*" or "zentivra" in agent.lower()
            elif in_our_section and line.lower().startswith("disallow:"):
                disallowed = line.split(":", 1)[1].strip()
                if disallowed and path.startswith(disallowed):
                    return False
        return True


class Fetcher:
    """
    Async content fetcher with retry, rate limiting, and robots.txt compliance.

    Usage:
        fetcher = Fetcher()
        result = await fetcher.fetch("https://example.com/blog")
        if result.success:
            logger.info("fetched_content content=%s", result.content)
    """

    def __init__(
        self,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
        respect_robots: bool = True,
    ):
        """Initialize fetcher with timeout, retry count, and robots.txt behavior."""
        configured_timeout = (
            timeout if timeout is not None else settings.http_fetch_timeout_seconds
        )
        configured_retries = (
            max_retries if max_retries is not None else settings.http_fetch_max_retries
        )
        self.timeout = max(1, int(configured_timeout))
        self.max_retries = max(1, int(configured_retries))
        self.respect_robots = respect_robots
        self._robots_checker = RobotsChecker()
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client. Reuses existing client if still open."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                },
                follow_redirects=True,
                timeout=httpx.Timeout(self.timeout),
            )
        return self._client

    async def fetch(
        self,
        url: str,
        rate_limit_rpm: int = 10,
        use_playwright_fallback: bool = True,
    ) -> FetchResult:
        """Fetch content from a URL.

        Flow: (1) Check robots.txt; (2) Apply rate limiting; (3) Fetch with httpx;
        (4) On 403/406/429 or JS-rendered content, try Playwright fallback;
        (5) Return FetchResult with content and hash.

        Args:
            url: URL to fetch.
            rate_limit_rpm: Max requests per minute per domain.
            use_playwright_fallback: Whether to try Playwright on bot-block or JS-heavy pages.

        Returns:
            FetchResult with content, status, and metadata. success=False on error.
        """
        client = await self._get_client()

        # Check robots.txt
        if self.respect_robots:
            allowed = await self._robots_checker.is_allowed(url, client)
            if not allowed:
                logger.warning("robots_disallowed url=%s", url)
                return FetchResult(
                    url=url,
                    status_code=403,
                    error="Blocked by robots.txt",
                    success=False,
                )

        # Rate limiting
        await rate_limiter.acquire(url, rate_limit_rpm)

        # Try httpx first
        result = await self._fetch_with_httpx(url, client)

        # Fallback to Playwright on bot-block status codes (403, 406, 429)
        if (
            use_playwright_fallback
            and not result.success
            and result.status_code in (403, 406, 429)
        ):
            logger.info(
                "playwright_fallback url=%s reason=HTTP %d",
                url,
                result.status_code,
            )
            pw_result = await self._fetch_with_playwright(url)
            if pw_result.success:
                return pw_result

        # Fallback to Playwright for JS-heavy pages
        if (
            use_playwright_fallback
            and result.success
            and self._seems_js_rendered(result.content)
        ):
            logger.info(
                "playwright_fallback url=%s reason=content seems JS-rendered", url
            )
            pw_result = await self._fetch_with_playwright(url)
            if pw_result.success and len(pw_result.content) > len(result.content):
                return pw_result

        return result

    async def _fetch_with_httpx(
        self, url: str, client: httpx.AsyncClient
    ) -> FetchResult:
        """Fetch using httpx with exponential backoff retry.

        Retries on 429/503 with 2^(attempt+1) second delay. On timeout/connect
        errors, retries up to max_retries times. Returns FetchResult with
        success=False and error message if all retries fail.
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                response = await client.get(url)
                content = response.text
                content_type = response.headers.get("content-type", "")

                if response.status_code >= 400:
                    logger.warning(
                        "fetch_http_error url=%s status=%d attempt=%d",
                        url,
                        response.status_code,
                        attempt + 1,
                    )
                    if (
                        response.status_code in (429, 503)
                        and attempt < self.max_retries - 1
                    ):
                        wait = 2 ** (attempt + 1)
                        await asyncio.sleep(wait)
                        continue

                    return FetchResult(
                        url=url,
                        status_code=response.status_code,
                        content=content,
                        content_type=content_type,
                        error=f"HTTP {response.status_code}",
                        success=False,
                    )

                redirected = str(response.url) if str(response.url) != url else None

                return FetchResult(
                    url=url,
                    status_code=response.status_code,
                    content=content,
                    content_type=content_type,
                    method="httpx",
                    redirected_url=redirected,
                    headers=dict(response.headers),
                )

            except httpx.TimeoutException as e:
                last_error = f"Timeout: {e}"
                logger.warning("fetch_timeout url=%s attempt=%d", url, attempt + 1)
            except httpx.ConnectError as e:
                last_error = f"Connection error: {e}"
                logger.warning(
                    "fetch_connect_error url=%s attempt=%d", url, attempt + 1
                )
            except Exception as e:
                last_error = str(e)
                logger.error(
                    "fetch_error url=%s error=%s attempt=%d", url, str(e), attempt + 1
                )

            if attempt < self.max_retries - 1:
                await asyncio.sleep(2 ** (attempt + 1))

        return FetchResult(
            url=url,
            status_code=0,
            error=last_error or "Max retries exceeded",
            success=False,
        )

    async def _fetch_with_playwright(self, url: str) -> FetchResult:
        """Fetch using Playwright for JavaScript-rendered pages.

        Uses sync_api in a thread (asyncio.to_thread) to avoid Windows asyncio
        subprocess issues. Returns FetchResult with success=False if Playwright
        is not installed or an error occurs.
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.warning("playwright_not_installed url=%s", url)
            return FetchResult(
                url=url, status_code=0, error="Playwright not installed", success=False
            )

        timeout_ms = max(self.timeout, 30) * 1000

        def _run_sync() -> FetchResult:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(user_agent=USER_AGENT)
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                    page.wait_for_timeout(2000)
                    content = page.content()
                    return FetchResult(
                        url=url,
                        status_code=200,
                        content=content,
                        method="playwright",
                    )
                finally:
                    browser.close()

        try:
            return await asyncio.to_thread(_run_sync)
        except Exception as e:
            logger.error("playwright_error url=%s error=%s", url, str(e))
            return FetchResult(
                url=url, status_code=0, error=f"Playwright error: {e}", success=False
            )

    def _seems_js_rendered(self, content: str) -> bool:
        """Heuristic: check if the page seems to be JavaScript-rendered (very little text)."""
        if not content:
            return True
        # Strip HTML tags and check text length
        import re

        text = re.sub(r"<[^>]+>", "", content)
        text = text.strip()
        # If the text content is very short relative to HTML, it's likely JS-rendered
        if len(text) < 200 and len(content) > 1000:
            return True
        # Check for common SPA indicators
        spa_indicators = [
            'id="__next"',  # Next.js
            'id="root"',  # React
            'id="app"',  # Vue
            "ng-app",  # Angular
            "noscript",
        ]
        text_ratio = len(text) / max(len(content), 1)
        if text_ratio < 0.05 and any(ind in content.lower() for ind in spa_indicators):
            return True
        return False

    async def fetch_many(
        self,
        urls: list[str],
        rate_limit_rpm: int = 10,
        max_concurrent: int = 5,
    ) -> list[FetchResult]:
        """Fetch multiple URLs with concurrency control.

        Args:
            urls: List of URLs to fetch.
            rate_limit_rpm: Max requests per minute per domain.
            max_concurrent: Max concurrent fetches (semaphore limit).

        Returns:
            List of FetchResult in same order as urls. Exceptions are
            converted to FetchResult with success=False and error set.
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def _bounded_fetch(url: str) -> FetchResult:
            async with semaphore:
                return await self.fetch(url, rate_limit_rpm)

        results = await asyncio.gather(
            *[_bounded_fetch(url) for url in urls],
            return_exceptions=True,
        )

        # Convert exceptions to FetchResults
        final = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final.append(
                    FetchResult(
                        url=urls[i],
                        status_code=0,
                        error=str(result),
                        success=False,
                    )
                )
            else:
                final.append(result)

        return final

    async def close(self):
        """Close the HTTP client. Safe to call if already closed."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
