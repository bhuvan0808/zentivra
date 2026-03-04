"""Quick verification test for Phase 2 core pipeline components."""
import asyncio
import sys

sys.path.insert(0, ".")


def test_imports():
    """Test that all core modules import correctly."""
    print("Testing imports...")
    from app.core.rate_limiter import RateLimiter, rate_limiter
    from app.core.fetcher import Fetcher, FetchResult
    from app.core.extractor import Extractor, ExtractionResult
    from app.core.change_detector import ChangeDetector, ChangeResult
    from app.core.summarizer import Summarizer, SummaryResult
    from app.core.dedup import DedupEngine, DedupResult
    from app.core.ranker import Ranker
    print("  ✅ All imports successful!")


def test_extractor():
    """Test HTML extraction."""
    print("\nTesting Extractor...")
    from app.core.extractor import Extractor

    extractor = Extractor()

    # Test HTML extraction
    html = """
    <html><head><title>Test Page</title></head>
    <body>
    <article>
        <h1>OpenAI Releases GPT-5</h1>
        <p>OpenAI has announced the release of GPT-5, their most capable model yet.
        The new model achieves state-of-the-art performance across all benchmarks.</p>
        <p>Key improvements include 2x longer context window and 40% faster inference.</p>
    </article>
    </body></html>
    """
    result = extractor.extract_html(html, "https://openai.com/blog/gpt-5")
    print(f"  Title: {result.title}")
    print(f"  Method: {result.method}")
    print(f"  Text length: {len(result.text)} chars")
    print(f"  Success: {result.success}")
    assert result.success, "Extraction should succeed"
    assert len(result.text) > 0, "Should extract text"
    print("  ✅ Extractor working!")


def test_change_detector():
    """Test change detection."""
    print("\nTesting Change Detector...")
    from app.core.change_detector import ChangeDetector

    detector = ChangeDetector()

    # Test identical content
    result = detector.compare("Hello world", "Hello world")
    assert not result.has_changed, "Identical content should not show change"
    print(f"  Same content → changed={result.has_changed} ✅")

    # Test different content
    result = detector.compare("Hello world v1", "Hello world v2 with updates")
    assert result.has_changed, "Different content should show change"
    print(f"  Different content → changed={result.has_changed}, ratio={result.change_ratio:.2f} ✅")

    # Test first fetch (no previous)
    result = detector.compare(None, "Brand new content")
    assert result.has_changed, "First fetch should be marked as changed"
    print(f"  First fetch → changed={result.has_changed} ✅")

    # Test significance
    assert detector.is_significant_change(result), "First fetch should be significant"
    print("  ✅ Change Detector working!")


def test_dedup():
    """Test deduplication."""
    print("\nTesting Dedup Engine...")
    from app.core.dedup import DedupEngine

    engine = DedupEngine()

    findings = [
        {"id": "1", "title": "GPT-5 Released", "summary_short": "OpenAI releases GPT-5", "confidence": 0.9},
        {"id": "2", "title": "GPT-5 Released", "summary_short": "OpenAI releases GPT-5", "confidence": 0.7},
        {"id": "3", "title": "Claude 4 Announced", "summary_short": "Anthropic announces Claude 4", "confidence": 0.8},
    ]

    result = engine.deduplicate(findings)
    print(f"  Input: {result.total_input}, Unique: {result.total_unique}, Dups: {result.total_duplicates}")
    assert result.total_duplicates >= 1, "Should find at least 1 duplicate"
    print("  ✅ Dedup Engine working!")


def test_ranker():
    """Test ranking."""
    print("\nTesting Ranker...")
    from app.core.ranker import Ranker

    ranker = Ranker(use_llm=False)  # Heuristic mode

    score = ranker.compute_impact_score(
        relevance=8, novelty=7, credibility=9, actionability=6
    )
    print(f"  Impact score (8,7,9,6): {score}")
    assert 0 <= score <= 1, "Score should be 0-1"
    print("  ✅ Ranker working!")


async def test_fetcher():
    """Test fetcher (requires network)."""
    print("\nTesting Fetcher...")
    from app.core.fetcher import Fetcher

    fetcher = Fetcher()
    result = await fetcher.fetch("https://httpbin.org/get", rate_limit_rpm=30, use_playwright_fallback=False)
    print(f"  Status: {result.status_code}")
    print(f"  Content length: {len(result.content)} chars")
    print(f"  Hash: {result.content_hash[:16]}...")
    print(f"  Method: {result.method}")
    assert result.success, "Fetch should succeed"
    await fetcher.close()
    print("  ✅ Fetcher working!")


if __name__ == "__main__":
    test_imports()
    test_extractor()
    test_change_detector()
    test_dedup()
    test_ranker()
    asyncio.run(test_fetcher())
    print("\n🎉 All Phase 2 components verified!")
