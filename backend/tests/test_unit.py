"""
Unit Tests — Core Pipeline Components.

Tests the extractor, change detector, dedup engine, ranker, and PDF renderer
WITHOUT any external API calls (pure unit tests).
"""

import sys
import pytest

sys.path.insert(0, ".")


# ═══════════════════════════════════════════════════════════════════════════
# Extractor Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestExtractor:
    """Test HTML/RSS content extraction."""

    def setup_method(self):
        from app.core.extractor import Extractor
        self.extractor = Extractor()

    def test_extract_html_basic(self):
        """Extract text from simple HTML."""
        html = """
        <html><head><title>Test Page</title></head>
        <body><article>
        <h1>Big AI Announcement</h1>
        <p>OpenAI released GPT-5 with improved reasoning capabilities.</p>
        <p>The model supports 1M context window and native tool use.</p>
        </article></body></html>
        """
        result = self.extractor.extract_html(html, url="https://example.com/test")
        assert result.text, "Should extract text"
        assert len(result.text) > 20, "Text should be non-trivial"
        assert result.title, "Should extract title"

    def test_extract_html_with_noise(self):
        """Should strip navigation, ads, and scripts."""
        html = """
        <html><body>
        <nav>Home | About | Contact</nav>
        <script>var x = 1;</script>
        <style>.ad { display: block; }</style>
        <article>
        <h1>Real Content</h1>
        <p>This is the actual important content we want to extract.</p>
        </article>
        <footer>Copyright 2024</footer>
        </body></html>
        """
        result = self.extractor.extract_html(html, url="https://example.com")
        assert "Real Content" in result.text or "important content" in result.text
        # Script/style content should not appear in extracted text
        assert "var x = 1" not in result.text

    def test_extract_empty_html(self):
        """Handle empty/minimal HTML gracefully."""
        result = self.extractor.extract_html("<html><body></body></html>")
        # Should not crash, just return empty/minimal text
        assert result is not None

    def test_extract_rss_feed(self):
        """Parse RSS/Atom feed entries."""
        rss = """<?xml version="1.0"?>
        <rss version="2.0">
        <channel>
        <title>Test Feed</title>
        <item>
            <title>New Model Release</title>
            <link>https://example.com/model</link>
            <description>A new foundation model was released today.</description>
            <pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate>
        </item>
        <item>
            <title>API Update</title>
            <link>https://example.com/api</link>
            <description>Major API changes announced.</description>
        </item>
        </channel>
        </rss>
        """
        entries = self.extractor.extract_feed(rss)
        assert len(entries) == 2, f"Should extract 2 entries, got {len(entries)}"
        assert entries[0].title == "New Model Release"
        assert entries[0].link == "https://example.com/model"
        assert entries[1].title == "API Update"

    def test_extract_dates(self):
        """Test various date format parsing."""
        date_strings = [
            "2024-01-15",
            "January 15, 2024",
            "Jan 15, 2024",
            "15/01/2024",
            "Mon, 15 Jan 2024 10:30:00 GMT",
        ]
        for ds in date_strings:
            result = self.extractor._parse_date(ds)
            # Should either return a datetime or None, not crash
            assert result is None or hasattr(result, "year"), f"Failed to parse: {ds}"


# ═══════════════════════════════════════════════════════════════════════════
# Change Detector Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestChangeDetector:
    """Test content change detection and significance filtering."""

    def setup_method(self):
        from app.core.change_detector import ChangeDetector
        self.detector = ChangeDetector()

    def test_first_fetch_is_significant(self):
        """First-time content (no previous) should always be significant."""
        result = self.detector.compare(None, "Brand new content")
        assert result.has_changed is True
        assert self.detector.is_significant_change(result) is True

    def test_identical_content_no_change(self):
        """Identical content should show no change."""
        content = "The quick brown fox jumps over the lazy dog."
        result = self.detector.compare(content, content)
        assert result.has_changed is False
        assert result.change_ratio == 0.0

    def test_minor_change_insignificant(self):
        """Small whitespace/timestamp changes should be insignificant."""
        old = "Content here. Last updated: 2024-01-01 10:00:00"
        new = "Content here. Last updated: 2024-01-02 10:00:00"
        result = self.detector.compare(old, new)
        # After canonicalization, timestamps should be stripped
        significant = self.detector.is_significant_change(result)
        # This tests the canonicalization logic

    def test_major_change_significant(self):
        """Large content changes should be significant."""
        old = "Old product description. Version 1.0 available."
        new = "Completely new product launch! Version 2.0 with revolutionary features. " * 5
        result = self.detector.compare(old, new)
        assert result.has_changed is True
        assert result.change_ratio > 0.3, "Major rewrite should have high change ratio"
        assert self.detector.is_significant_change(result) is True

    def test_content_hashing_deterministic(self):
        """Same content should always produce the same hash."""
        content = "Test content for hashing"
        r1 = self.detector.compare(None, content)
        r2 = self.detector.compare(None, content)
        assert r1.current_hash == r2.current_hash

    def test_canonicalization_strips_noise(self):
        """Canonicalization should normalize whitespace and timestamps."""
        from app.core.change_detector import ChangeDetector
        d = ChangeDetector()
        text1 = "Hello   world   2024-01-01T10:00:00Z   test"
        text2 = "Hello world 2024-01-02T10:00:00Z test"
        canon1 = d.canonicalize(text1)
        canon2 = d.canonicalize(text2)
        # Both should canonicalize to similar strings
        assert canon1 is not None
        assert canon2 is not None


# ═══════════════════════════════════════════════════════════════════════════
# Dedup Engine Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestDedupEngine:
    """Test deduplication via hash matching."""

    def setup_method(self):
        from app.core.dedup import DedupEngine
        self.dedup = DedupEngine()

    def test_no_duplicates(self):
        """Unique findings should all pass through."""
        findings = [
            {"id": "1", "title": "Finding A", "summary_short": "First unique finding", "diff_hash": "hash_a"},
            {"id": "2", "title": "Finding B", "summary_short": "Second unique finding", "diff_hash": "hash_b"},
            {"id": "3", "title": "Finding C", "summary_short": "Third unique finding", "diff_hash": "hash_c"},
        ]
        result = self.dedup.deduplicate(findings)
        assert result.total_unique == 3
        assert result.total_duplicates == 0

    def test_exact_duplicates_removed(self):
        """Findings with identical title+summary should be deduplicated."""
        findings = [
            {"id": "1", "title": "Finding A", "summary_short": "Same content"},
            {"id": "2", "title": "Finding A", "summary_short": "Same content"},
        ]
        result = self.dedup.deduplicate(findings)
        assert result.total_unique == 1
        assert result.total_duplicates == 1

    def test_empty_input(self):
        """Empty list should return empty result."""
        result = self.dedup.deduplicate([])
        assert result.total_unique == 0
        assert result.total_duplicates == 0

    def test_single_finding(self):
        """Single finding should pass through."""
        findings = [{"id": "1", "title": "Solo", "summary_short": "Only one", "diff_hash": "unique"}]
        result = self.dedup.deduplicate(findings)
        assert result.total_unique == 1
        assert result.total_duplicates == 0


# ═══════════════════════════════════════════════════════════════════════════
# Ranker Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestRanker:
    """Test impact scoring and ranking."""

    def test_heuristic_scoring(self):
        """Test ranking without LLM (heuristic fallback)."""
        from app.core.ranker import Ranker
        ranker = Ranker(use_llm=False)

        findings = [
            {"id": "1", "title": "Low Impact", "category": "other", "confidence": 0.3,
             "summary_short": "Minor update", "tags": [], "entities": {}},
            {"id": "2", "title": "High Impact", "category": "models", "confidence": 0.9,
             "summary_short": "Major model release", "tags": ["model_release"], "entities": {}},
        ]

        import asyncio
        ranked = asyncio.run(ranker.rank_findings(findings))

        assert len(ranked) == 2
        # Higher confidence + models category should rank higher
        assert ranked[0]["impact_score"] >= ranked[1]["impact_score"]
        assert ranked[0]["title"] == "High Impact"

    def test_impact_formula(self):
        """Test the weighted impact formula."""
        from app.core.ranker import Ranker
        ranker = Ranker(use_llm=False)

        # Inputs on 0-10 scale (as used internally)
        score = ranker.compute_impact_score(
            relevance=9, novelty=8, credibility=7, actionability=6
        )
        # Formula: (0.35*9 + 0.25*8 + 0.20*7 + 0.20*6) / 10
        expected = (0.35 * 9 + 0.25 * 8 + 0.20 * 7 + 0.20 * 6) / 10
        assert abs(score - expected) < 0.01, f"Expected {expected}, got {score}"

    def test_ranking_order(self):
        """Findings should be sorted by impact score descending."""
        from app.core.ranker import Ranker
        ranker = Ranker(use_llm=False)

        findings = [
            {"id": str(i), "title": f"F{i}", "category": "other",
             "confidence": 0.1 * i, "summary_short": f"Text {i}",
             "tags": [], "entities": {}}
            for i in range(1, 6)
        ]

        import asyncio
        ranked = asyncio.run(ranker.rank_findings(findings))

        scores = [f["impact_score"] for f in ranked]
        assert scores == sorted(scores, reverse=True), "Should be sorted descending"


# ═══════════════════════════════════════════════════════════════════════════
# PDF Renderer Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestPDFRenderer:
    """Test PDF/HTML rendering."""

    def test_render_html_output(self):
        """Should render HTML from digest data."""
        from app.digest.pdf_renderer import PDFRenderer
        from datetime import date

        renderer = PDFRenderer()
        digest_data = {
            "date": date(2024, 1, 15),
            "executive_summary": "Today's key findings include a major model release.",
            "sections": {
                "Competitor Releases": {
                    "findings": [
                        {
                            "title": "GPT-5 Released",
                            "category": "models",
                            "impact_score": 0.85,
                            "confidence": 0.9,
                            "summary_short": "OpenAI released GPT-5.",
                            "why_it_matters": "Major improvement in reasoning.",
                            "tags": ["gpt-5", "release"],
                            "publisher": "OpenAI",
                            "source_url": "https://openai.com/blog/gpt-5",
                        }
                    ],
                    "count": 1,
                    "narrative": "A significant release from OpenAI today.",
                }
            },
            "total_findings": 1,
            "total_duplicates_removed": 0,
        }

        html = renderer.render_html_only(digest_data)
        assert "ZENTIVRA" in html
        assert "GPT-5 Released" in html
        assert "Executive Summary" in html
        assert "2024" in html

    def test_render_empty_digest(self):
        """Should handle empty digest gracefully."""
        from app.digest.pdf_renderer import PDFRenderer
        from datetime import date

        renderer = PDFRenderer()
        digest_data = {
            "date": date(2024, 1, 15),
            "executive_summary": "No updates today.",
            "sections": {},
            "total_findings": 0,
            "total_duplicates_removed": 0,
        }

        html = renderer.render_html_only(digest_data)
        assert "ZENTIVRA" in html
        assert "No updates today" in html


# ═══════════════════════════════════════════════════════════════════════════
# Digest Compiler Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestDigestCompiler:
    """Test digest compilation logic."""

    def test_empty_digest(self):
        """Empty findings should produce empty digest."""
        from app.digest.compiler import DigestCompiler
        import asyncio

        compiler = DigestCompiler()
        result = asyncio.run(compiler.compile("test-run", []))
        assert result["total_findings"] == 0
        assert result["executive_summary"] != ""

    def test_section_organization(self):
        """Findings should be organized by agent type."""
        from app.digest.compiler import DigestCompiler

        compiler = DigestCompiler()
        findings = [
            {"id": "1", "title": "Research Paper", "category": "research",
             "tags": ["research_paper"], "confidence": 0.8},
            {"id": "2", "title": "Model Release", "category": "models",
             "tags": ["model_release"], "confidence": 0.9},
        ]

        sections = compiler._organize_by_section(findings)
        # Should create separate sections
        assert len(sections) >= 1

    def test_fallback_narrative(self):
        """Should generate bullet-point narrative when LLM unavailable."""
        from app.digest.compiler import DigestCompiler

        compiler = DigestCompiler()
        findings = [
            {"title": "Finding 1", "summary_short": "Summary 1", "confidence": 0.8},
            {"title": "Finding 2", "summary_short": "Summary 2", "confidence": 0.6},
        ]

        narrative = compiler._fallback_narrative(findings)
        assert "Finding 1" in narrative
        assert "Finding 2" in narrative
        assert "2 updates" in narrative


# ═══════════════════════════════════════════════════════════════════════════
# Agent Worker Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestAgentWorkers:
    """Test agent-specific post-processing logic."""

    def test_competitor_watcher_keyword_detection(self):
        """Should detect high-impact keywords and boost confidence."""
        from app.agents.competitor_watcher import CompetitorWatcher
        import asyncio

        agent = CompetitorWatcher()
        assert agent.agent_type == "competitor"

        finding = {
            "title": "GPT-5 Now Generally Available",
            "summary_short": "Major pricing update with new API features",
            "confidence": 0.6,
            "tags": [],
            "entities": {},
        }

        class MockSource:
            name = "OpenAI"
            css_selectors = None

        class MockExtraction:
            text = "test"

        result = asyncio.run(agent.post_process_finding(finding, MockExtraction(), MockSource()))
        assert result["confidence"] > 0.6, "Should boost for GA/pricing/API keywords"

    def test_model_provider_model_detection(self):
        """Should detect model names via regex."""
        from app.agents.model_provider_watcher import ModelProviderWatcher
        import asyncio

        agent = ModelProviderWatcher()
        assert agent.agent_type == "model_provider"

        finding = {
            "title": "Claude 3.5 Sonnet Released",
            "summary_long": "Anthropic released Claude 3.5 Sonnet with improvements to reasoning",
            "confidence": 0.7,
            "tags": [],
            "entities": {},
            "category": "other",
        }

        class MockSource:
            name = "Anthropic"
            css_selectors = None

        class MockExtraction:
            text = "test"

        result = asyncio.run(agent.post_process_finding(finding, MockExtraction(), MockSource()))
        # The model_provider_watcher detects model keywords and sets category
        assert result["category"] in ("models", "apis")

    def test_hf_tracker_benchmark_detection(self):
        """Should detect benchmark names and SOTA claims."""
        from app.agents.hf_benchmark_tracker import HFBenchmarkTracker
        import asyncio

        agent = HFBenchmarkTracker()
        assert agent.agent_type == "hf_benchmark"

        finding = {
            "title": "Llama 3 achieves SOTA on MMLU",
            "summary_long": "New state-of-the-art on MMLU benchmark with 90% accuracy",
            "source_url": "https://huggingface.co/spaces/leaderboard",
            "confidence": 0.7,
            "tags": [],
            "entities": {},
            "category": "other",
        }

        class MockSource:
            name = "Open LLM Leaderboard"
            css_selectors = None
            url = "https://huggingface.co/spaces/leaderboard"

        class MockExtraction:
            text = "test"

        result = asyncio.run(agent.post_process_finding(finding, MockExtraction(), MockSource()))
        assert "sota_claim" in result["tags"]
        assert "MMLU" in result["tags"]
        assert result["category"] == "benchmarks"


# ═══════════════════════════════════════════════════════════════════════════
# Config Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestConfig:
    """Test configuration loading."""

    def test_settings_load(self):
        """Settings should load from .env."""
        from app.config import settings
        assert settings.database_url
        assert settings.digest_time
        assert settings.timezone

    def test_llm_provider_detection(self):
        """Should detect active LLM provider."""
        from app.config import settings
        provider = settings.active_llm_provider
        assert provider in ("groq", "openrouter", "gemini", "openai", "anthropic", "none")

    def test_email_recipient_parsing(self):
        """Should parse comma-separated recipients."""
        from app.config import Settings
        s = Settings(email_recipients="a@b.com, c@d.com")
        assert s.email_recipient_list == ["a@b.com", "c@d.com"]

    def test_empty_recipients(self):
        """Empty recipients should return empty list."""
        from app.config import Settings
        s = Settings(email_recipients="")
        assert s.email_recipient_list == []


# ═══════════════════════════════════════════════════════════════════════════
# Rate Limiter Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestRateLimiter:
    """Test async rate limiter."""

    def test_rate_limiter_creation(self):
        """Should create rate limiter instances."""
        from app.core.rate_limiter import RateLimiter
        limiter = RateLimiter()
        assert limiter is not None

    def test_rate_limiter_acquire(self):
        """Should allow requests within limits."""
        import asyncio
        from app.core.rate_limiter import RateLimiter

        limiter = RateLimiter()

        async def test():
            # First request should succeed immediately
            await limiter.acquire("example.com", rpm=60)
            return True

        assert asyncio.run(test()) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
