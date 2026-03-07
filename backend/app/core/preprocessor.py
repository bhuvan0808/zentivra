"""Content Preprocessor Layer.

Runs after HTML extraction and before AI summarization to normalize text,
remove boilerplate, and produce cleaner input for LLM processing.
"""

import re
import unicodedata
from html import unescape
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

MAX_CONTENT_LENGTH = 25_000

BOILERPLATE_PATTERNS = [
    re.compile(r"(?i)accept\s+(all\s+)?cookies?"),
    re.compile(r"(?i)we\s+use\s+cookies"),
    re.compile(r"(?i)cookie\s+(policy|preferences|settings|consent)"),
    re.compile(r"(?i)privacy\s+policy"),
    re.compile(r"(?i)terms\s+(of\s+)?(service|use)"),
    re.compile(r"(?i)subscribe\s+to\s+(our\s+)?newsletter"),
    re.compile(r"(?i)sign\s+up\s+for\s+(our\s+)?(newsletter|updates)"),
    re.compile(r"(?i)follow\s+us\s+on"),
    re.compile(r"(?i)share\s+(this|on)\s+(twitter|facebook|linkedin|x)"),
    re.compile(r"(?i)©\s*\d{4}"),
    re.compile(r"(?i)all\s+rights\s+reserved"),
    re.compile(r"(?i)skip\s+to\s+(main\s+)?content"),
    re.compile(r"(?i)back\s+to\s+top"),
    re.compile(r"(?i)loading\.{2,}"),
    re.compile(r"(?i)please\s+enable\s+javascript"),
]

TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "ref", "fbclid", "gclid", "mc_cid", "mc_eid", "spm",
}

MIN_LINE_LENGTH = 4


def preprocess(text: str, *, max_length: int = MAX_CONTENT_LENGTH) -> str:
    """Full preprocessing pipeline: normalize -> clean -> truncate."""
    if not text:
        return ""

    text = _normalize_unicode(text)
    text = _strip_html_entities(text)
    text = _clean_urls_in_text(text)
    text = _remove_boilerplate_lines(text)
    text = _remove_short_lines(text)
    text = _collapse_whitespace(text)
    text = text.strip()

    if len(text) > max_length:
        text = text[:max_length].rsplit(" ", 1)[0] + " ..."

    return text


def _normalize_unicode(text: str) -> str:
    return unicodedata.normalize("NFKC", text)


def _strip_html_entities(text: str) -> str:
    return unescape(text)


def _clean_urls_in_text(text: str) -> str:
    """Strip tracking query parameters from URLs embedded in text."""

    def _clean_url(match: re.Match) -> str:
        url = match.group(0)
        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query, keep_blank_values=True)
            cleaned = {k: v for k, v in params.items() if k.lower() not in TRACKING_PARAMS}
            new_query = urlencode(cleaned, doseq=True) if cleaned else ""
            return urlunparse(parsed._replace(query=new_query))
        except Exception:
            return url

    return re.sub(r"https?://[^\s)>\]\"']+", _clean_url, text)


def _remove_boilerplate_lines(text: str) -> str:
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if any(pat.search(stripped) for pat in BOILERPLATE_PATTERNS):
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


def _remove_short_lines(text: str) -> str:
    """Remove lines shorter than MIN_LINE_LENGTH that look like UI artifacts."""
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            cleaned.append(line)
            continue
        if len(stripped) < MIN_LINE_LENGTH and not stripped[0].isdigit():
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


def _collapse_whitespace(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text
