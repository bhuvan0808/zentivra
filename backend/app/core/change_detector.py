"""
Change Detector - Content diffing and fingerprinting.

Detects whether a page has changed since the last fetch by comparing
content hashes. If changed, generates a human-readable diff.
"""

from dataclasses import dataclass
import difflib
import hashlib
import re
from typing import Optional

from app.utils.logger import logger


@dataclass
class ChangeResult:
    """Result of change detection between two content versions."""

    has_changed: bool
    current_hash: str
    previous_hash: Optional[str] = None
    diff_text: Optional[str] = None
    diff_summary: Optional[str] = None
    added_lines: int = 0
    removed_lines: int = 0
    change_ratio: float = 0.0  # 0 = identical, 1 = completely different


class ChangeDetector:
    """
    Detect changes between content snapshots using hashing and diffing.

    Usage:
        detector = ChangeDetector()
        result = detector.compare("old content", "new content")
        if result.has_changed:
            logger.info("diff_text diff=%s", result.diff_text)
    """

    def canonicalize(self, text: str) -> str:
        """
        Canonicalize text for stable hashing.

        Removes noise that doesn't represent real content changes:
        - Extra whitespace
        - JavaScript timestamps
        - Session tokens
        - Ad/tracking content
        """
        if not text:
            return ""

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text)
        text = text.strip()

        # Remove common dynamic content patterns
        # Timestamps like "2024-01-15T10:30:00Z" or "Jan 15, 2024 10:30 AM"
        text = re.sub(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[Z+\-\d:]*", "[TIMESTAMP]", text
        )

        # Remove session-like tokens (long hex/base64 strings)
        text = re.sub(r"[a-f0-9]{32,}", "[TOKEN]", text)

        # Remove common tracking parameters
        text = re.sub(r"utm_\w+=[^&\s]+", "", text)
        text = re.sub(r"ref=[^&\s]+", "", text)

        return text

    def compute_hash(self, content: str, canonicalize: bool = True) -> str:
        """Compute SHA256 hash of content, optionally canonicalized."""
        if canonicalize:
            content = self.canonicalize(content)
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def compare(
        self,
        previous_content: Optional[str],
        current_content: str,
        context_lines: int = 3,
    ) -> ChangeResult:
        """
        Compare two content versions and detect changes.

        Args:
            previous_content: Previous version (None if first fetch)
            current_content: Current version
            context_lines: Number of context lines in diff

        Returns:
            ChangeResult with diff details
        """
        current_hash = self.compute_hash(current_content)

        # First fetch — no previous content to compare
        if previous_content is None:
            return ChangeResult(
                has_changed=True,  # New content is always "changed"
                current_hash=current_hash,
                previous_hash=None,
                diff_summary="New content (first fetch)",
                change_ratio=1.0,
            )

        previous_hash = self.compute_hash(previous_content)

        # Quick hash comparison
        if current_hash == previous_hash:
            return ChangeResult(
                has_changed=False,
                current_hash=current_hash,
                previous_hash=previous_hash,
                change_ratio=0.0,
            )

        # Content changed — generate diff
        prev_lines = self.canonicalize(previous_content).splitlines()
        curr_lines = self.canonicalize(current_content).splitlines()

        diff = list(
            difflib.unified_diff(
                prev_lines,
                curr_lines,
                lineterm="",
                n=context_lines,
            )
        )

        # Count additions and removals
        added = sum(
            1 for line in diff if line.startswith("+") and not line.startswith("+++")
        )
        removed = sum(
            1 for line in diff if line.startswith("-") and not line.startswith("---")
        )

        # Compute change ratio using SequenceMatcher
        matcher = difflib.SequenceMatcher(None, prev_lines, curr_lines)
        change_ratio = 1.0 - matcher.ratio()

        diff_text = "\n".join(diff) if diff else None

        # Generate summary
        diff_summary = (
            f"{added} lines added, {removed} lines removed ({change_ratio:.1%} changed)"
        )

        logger.info(
            "change_detected added=%d removed=%d ratio=%.3f",
            added,
            removed,
            change_ratio,
        )

        return ChangeResult(
            has_changed=True,
            current_hash=current_hash,
            previous_hash=previous_hash,
            diff_text=diff_text,
            diff_summary=diff_summary,
            added_lines=added,
            removed_lines=removed,
            change_ratio=change_ratio,
        )

    def is_significant_change(
        self,
        change_result: ChangeResult,
        min_change_ratio: float = 0.01,
        min_changed_lines: int = 2,
    ) -> bool:
        """
        Determine if a change is significant enough to warrant re-summarization.

        Filters out trivial changes (e.g., just a timestamp update).
        First-fetch (no previous content) is always significant.
        """
        if not change_result.has_changed:
            return False

        # First fetch — always significant
        if change_result.previous_hash is None:
            return True

        total_changed = change_result.added_lines + change_result.removed_lines
        return (
            change_result.change_ratio >= min_change_ratio
            and total_changed >= min_changed_lines
        )
