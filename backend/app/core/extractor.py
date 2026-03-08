"""Extractor layer — content extraction from HTML and feeds.

Second stage of the pipeline: fetch -> extract -> preprocess -> summarize -> dedup -> rank.

Handles:
- HTML pages → clean article text via trafilatura + BeautifulSoup
- RSS/Atom feeds → feed entries via feedparser
- Metadata extraction (title, date, author, etc.)
"""

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urljoin

from app.utils.logger import logger


@dataclass
class ExtractionResult:
    """Result of content extraction from HTML or other formats.

    Attributes:
        text: Extracted main text content.
        title: Page/article title.
        date: Publication date if available.
        author: Author if available.
        description: Meta description or summary.
        method: Extraction method used ("trafilatura", "beautifulsoup", "css_selectors", etc.).
        links: List of URLs found in the content (limited to 50).
        metadata: Additional metadata (e.g., source_url, selectors_used).
        success: True if extraction succeeded.
        error: Error message if success=False.
    """

    text: str = ""
    title: Optional[str] = None
    date: Optional[datetime] = None
    author: Optional[str] = None
    description: Optional[str] = None
    method: str = "unknown"
    links: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None


@dataclass
class FeedEntry:
    """A single entry from an RSS/Atom feed.

    Attributes:
        title: Entry title.
        link: Entry URL.
        published: Publication datetime if available.
        summary: Entry summary/description.
        author: Author if available.
        tags: List of tag terms.
    """

    title: str
    link: str
    published: Optional[datetime] = None
    summary: str = ""
    author: Optional[str] = None
    tags: list[str] = field(default_factory=list)


class Extractor:
    """Multi-format content extractor for HTML and RSS/Atom feeds.

    Usage:
        extractor = Extractor()
        result = extractor.extract_html(html_content, url)
        entries = extractor.extract_feed(feed_content)
    """

    def extract_html(
        self,
        html: str,
        url: str = "",
        css_selectors: dict | None = None,
    ) -> ExtractionResult:
        """Extract clean text from HTML content.

        Strategy: (1) If css_selectors provided, use BeautifulSoup; (2) Else
        trafilatura for article extraction; (3) Fallback to BeautifulSoup generic.

        Args:
            html: Raw HTML string.
            url: Source URL for link resolution and metadata.
            css_selectors: Optional dict with keys "title", "content", "date".

        Returns:
            ExtractionResult with text, title, date, etc. success=False if empty.
        """
        if not html or not html.strip():
            return ExtractionResult(
                success=False, error="Empty HTML content", method="none"
            )

        # Strategy 1: Use CSS selectors if provided
        if css_selectors:
            result = self._extract_with_selectors(html, css_selectors, url)
            if result.success and result.text:
                return result

        # Strategy 2: Use trafilatura (best for article pages)
        result = self._extract_with_trafilatura(html, url)
        if result.success and result.text and len(result.text) > 100:
            return result

        # Strategy 3: BeautifulSoup fallback
        result = self._extract_with_beautifulsoup(html, url)
        return result

    def _extract_with_trafilatura(self, html: str, url: str) -> ExtractionResult:
        """Extract article content using trafilatura.

        Returns ExtractionResult with success=False if trafilatura returns empty
        or is not installed. Extracts metadata (title, author, date) from JSON output.
        """
        try:
            import trafilatura

            # Extract main content
            text = trafilatura.extract(
                html,
                url=url,
                include_comments=False,
                include_tables=True,
                no_fallback=False,
                favor_precision=True,
            )

            if not text:
                return ExtractionResult(
                    success=False,
                    error="Trafilatura returned empty",
                    method="trafilatura",
                )

            # Extract metadata
            metadata = trafilatura.extract(
                html,
                url=url,
                output_format="json",
                include_comments=False,
            )

            title = None
            date = None
            author = None

            if metadata:
                import json

                try:
                    meta_dict = (
                        json.loads(metadata) if isinstance(metadata, str) else metadata
                    )
                    title = meta_dict.get("title")
                    author = meta_dict.get("author")
                    date_str = meta_dict.get("date")
                    if date_str:
                        try:
                            date = datetime.fromisoformat(date_str)
                        except (ValueError, TypeError):
                            pass
                except (json.JSONDecodeError, AttributeError):
                    pass

            # If no title from trafilatura, extract from HTML
            if not title:
                title = self._extract_title(html)

            return ExtractionResult(
                text=text,
                title=title,
                date=date,
                author=author,
                method="trafilatura",
                metadata={"source_url": url},
            )

        except ImportError:
            logger.warning("trafilatura_not_installed")
            return ExtractionResult(
                success=False, error="trafilatura not installed", method="trafilatura"
            )
        except Exception as e:
            logger.error("trafilatura_error error=%s", str(e))
            return ExtractionResult(success=False, error=str(e), method="trafilatura")

    def _extract_with_selectors(
        self, html: str, selectors: dict, url: str
    ) -> ExtractionResult:
        """Extract content using CSS selectors.

        Expects selectors dict with keys: title, content, date (optional).
        Returns ExtractionResult with success=False on exception.
        """
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html, "html.parser")

            title = None
            text_parts = []

            # Extract title
            if "title" in selectors:
                title_el = soup.select_one(selectors["title"])
                if title_el:
                    title = title_el.get_text(strip=True)

            # Extract content
            if "content" in selectors:
                content_els = soup.select(selectors["content"])
                for el in content_els:
                    text_parts.append(el.get_text(separator="\n", strip=True))

            # Extract date
            date = None
            if "date" in selectors:
                date_el = soup.select_one(selectors["date"])
                if date_el:
                    date = self._parse_date(date_el.get_text(strip=True))

            text = "\n\n".join(text_parts)

            if not title:
                title = self._extract_title(html)

            return ExtractionResult(
                text=text,
                title=title,
                date=date,
                method="css_selectors",
                metadata={"selectors_used": selectors, "source_url": url},
                success=bool(text),
            )

        except Exception as e:
            logger.error("selector_extraction_error error=%s", str(e))
            return ExtractionResult(success=False, error=str(e), method="css_selectors")

    def _extract_with_beautifulsoup(self, html: str, url: str) -> ExtractionResult:
        """Fallback: extract content using BeautifulSoup.

        Removes script/style/nav/footer/header; finds main/article/body.
        Extracts links (up to 50). Returns ExtractionResult with success=False on exception.
        """
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html, "html.parser")

            # Remove script, style, nav, footer, header elements
            for tag in soup.find_all(
                ["script", "style", "nav", "footer", "header", "aside", "noscript"]
            ):
                tag.decompose()

            # Try to find main content area
            main_content = (
                soup.find("main")
                or soup.find("article")
                or soup.find(attrs={"role": "main"})
                or soup.find(class_=re.compile(r"(content|article|post|entry)", re.I))
                or soup.body
                or soup
            )

            text = (
                main_content.get_text(separator="\n", strip=True)
                if main_content
                else ""
            )

            # Clean up the text
            text = re.sub(r"\n{3,}", "\n\n", text)
            text = re.sub(r" {2,}", " ", text)

            # Extract links
            links = []
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.startswith(("http://", "https://")):
                    links.append(href)
                elif href.startswith("/") and url:
                    links.append(urljoin(url, href))

            title = self._extract_title(html)

            return ExtractionResult(
                text=text,
                title=title,
                method="beautifulsoup",
                links=links[:50],  # Limit to 50 links
                metadata={"source_url": url},
                success=bool(text),
            )

        except Exception as e:
            logger.error("beautifulsoup_error error=%s", str(e))
            return ExtractionResult(success=False, error=str(e), method="beautifulsoup")

    def extract_feed(self, content: str, feed_url: str = "") -> list[FeedEntry]:
        """Extract entries from an RSS/Atom feed.

        Args:
            content: Raw feed XML string.
            feed_url: Feed URL (for logging).

        Returns:
            List of FeedEntry. Returns [] on parse error.
        """
        try:
            import feedparser

            feed = feedparser.parse(content)
            entries = []

            for entry in feed.entries:
                published = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    try:
                        import time

                        published = datetime.fromtimestamp(
                            time.mktime(entry.published_parsed), tz=timezone.utc
                        )
                    except (TypeError, ValueError, OverflowError):
                        pass

                tags = []
                if hasattr(entry, "tags"):
                    tags = [t.get("term", "") for t in entry.tags if t.get("term")]

                entries.append(
                    FeedEntry(
                        title=getattr(entry, "title", "Untitled"),
                        link=getattr(entry, "link", ""),
                        published=published,
                        summary=getattr(entry, "summary", ""),
                        author=getattr(entry, "author", None),
                        tags=tags,
                    )
                )

            logger.info("feed_extracted url=%s entries=%d", feed_url, len(entries))
            return entries

        except Exception as e:
            logger.error("feed_extraction_error url=%s error=%s", feed_url, str(e))
            return []

    def _extract_title(self, html: str) -> Optional[str]:
        """Extract page title from HTML. Tries og:title, <title>, then first h1."""
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html, "html.parser")
            # Try og:title first
            og_title = soup.find("meta", property="og:title")
            if og_title and og_title.get("content"):
                return og_title["content"]
            # Then <title> tag
            if soup.title and soup.title.string:
                return soup.title.string.strip()
            # Then first h1
            h1 = soup.find("h1")
            if h1:
                return h1.get_text(strip=True)
        except Exception:
            pass
        return None

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Try to parse a date string in various formats. Returns None if unparseable."""
        import re
        from datetime import datetime

        formats = [
            "%Y-%m-%d",
            "%B %d, %Y",
            "%b %d, %Y",
            "%d %B %Y",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S%z",
            "%m/%d/%Y",
            "%d/%m/%Y",
        ]

        date_str = date_str.strip()
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None
