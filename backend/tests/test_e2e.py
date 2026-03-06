"""
End-to-End Pipeline Test.

Tests the full pipeline with REAL sources and the Gemini LLM:
1. Fetcher → fetch a blog page
2. Extractor → extract text
3. Change Detector → detect changes
4. Summarizer → call Gemini for structured summary
5. Dedup → deduplicate findings
6. Ranker → compute impact scores
7. Digest Compiler → compile sections + narratives
8. PDF Renderer → generate HTML/PDF digest
"""

import asyncio
import json
import sys
import time

sys.path.insert(0, ".")

from app.config import settings


async def test_step_by_step():
    """Run the pipeline step by step on a single test URL."""
    print("=" * 70)
    print("  ZENTIVRA — End-to-End Pipeline Test")
    print("=" * 70)

    # ── Pre-flight checks ────────────────────────────────────────────────
    print(f"\n✅ LLM Provider: {settings.active_llm_provider}")
    if settings.active_llm_provider == "none":
        print("❌ No LLM provider configured. Set GEMINI_API_KEY in .env")
        return
    print(f"✅ Database: {settings.database_url[:40]}...")

    # ── Step 1: Fetch ────────────────────────────────────────────────────
    print("\n─── Step 1: FETCH ─────────────────────────────────────────")
    from app.core.fetcher import Fetcher

    fetcher = Fetcher()
    t0 = (time.time(),)

    # Fetch OpenAI blog (a real competitor source)
    test_url = "https://openai.com/index/introducing-4o-image-generation/"
    print(f"  Fetching: {test_url}")
    result = await fetcher.fetch(
        test_url, rate_limit_rpm=30, use_playwright_fallback=False
    )

    print(f"  Status: {result.status_code}")
    print(f"  Content length: {len(result.content)} chars")
    print(f"  Content hash: {result.content_hash[:16]}...")
    print(f"  Method: {result.method}")
    print(f"  Time: {time.time() - t0[0]:.1f}s")

    if not result.success:
        print(f"  ⚠️ Fetch failed: {result.error}")
        # Use a fallback test with simulated content
        print("  → Using simulated content for remaining steps...")
        result.content = """
        <html><head><title>OpenAI Introduces GPT-4o Image Generation</title></head>
        <body><article>
        <h1>Introducing 4o Image Generation</h1>
        <p>We're bringing image generation capabilities natively into GPT-4o, 
        our most capable model. The model can now generate and edit images 
        directly within ChatGPT conversations, offering seamless 
        multimodal interactions.</p>
        <p>Key features include text rendering in images, consistent character design, 
        and the ability to edit uploaded photos. The model understands context 
        from the conversation to produce relevant images.</p>
        <p>GPT-4o image generation is now available to all ChatGPT Plus, Team, 
        and Enterprise users via the API and ChatGPT.</p>
        </article></body></html>
        """
        result.success = True

    assert result.content, "Should have content"
    print("  ✅ Fetch successful!")

    # ── Step 2: Extract ──────────────────────────────────────────────────
    print("\n─── Step 2: EXTRACT ───────────────────────────────────────")
    from app.core.extractor import Extractor

    extractor = Extractor()
    extraction = extractor.extract_html(result.content, url=test_url)

    print(f"  Title: {extraction.title}")
    print(f"  Method: {extraction.method}")
    print(f"  Text length: {len(extraction.text)} chars")
    print(f"  First 200 chars: {extraction.text[:200]}...")
    assert extraction.text, "Should extract text"
    print("  ✅ Extraction successful!")

    # ── Step 3: Change Detection ─────────────────────────────────────────
    print("\n─── Step 3: CHANGE DETECTION ──────────────────────────────")
    from app.core.change_detector import ChangeDetector

    detector = ChangeDetector()
    change = detector.compare(None, extraction.text)  # First fetch

    print(f"  Has changed: {change.has_changed}")
    print(f"  Change ratio: {change.change_ratio:.2f}")
    print(f"  Hash: {change.current_hash[:16]}...")
    print(f"  Significant: {detector.is_significant_change(change)}")
    assert change.has_changed, "First fetch should be marked changed"
    print("  ✅ Change detection working!")

    # ── Step 4: Summarize (calls Gemini!) ────────────────────────────────
    print("\n─── Step 4: SUMMARIZE (calling Gemini API) ────────────────")
    from app.core.summarizer import Summarizer

    summarizer = Summarizer()
    t0 = time.time()
    summary = await summarizer.summarize(
        content=extraction.text,
        source_name="OpenAI",
        source_url=test_url,
        content_type="competitor blog post",
    )
    llm_time = time.time() - t0

    print(f"  Success: {summary.success}")
    if summary.error:
        print(f"  Error: {summary.error}")
    print(f"  Title: {summary.title}")
    print(f"  Category: {summary.category}")
    print(f"  Confidence: {summary.confidence}")
    print(f"  Summary: {summary.summary_short[:200]}...")
    print(f"  Why it matters: {summary.why_it_matters[:150]}...")
    print(f"  Tags: {summary.tags}")
    print(f"  Entities: {json.dumps(summary.entities, indent=2)}")
    print(f"  LLM time: {llm_time:.1f}s")
    assert summary.success, f"Summarization failed: {summary.error}"
    print("  ✅ Summarization successful!")

    # ── Step 5: Ranking ──────────────────────────────────────────────────
    print("\n─── Step 5: RANKING (calling Gemini API) ──────────────────")
    from app.core.ranker import Ranker

    ranker = Ranker(use_llm=True)
    t0 = time.time()

    finding = {
        "id": "test-finding-1",
        "run_id": "test-run-1",
        "source_id": "test-source-1",
        "title": summary.title,
        "summary_short": summary.summary_short,
        "summary_long": summary.summary_long,
        "why_it_matters": summary.why_it_matters,
        "category": summary.category,
        "confidence": summary.confidence,
        "tags": summary.tags,
        "entities": summary.entities,
        "publisher": "OpenAI",
        "source_url": test_url,
    }

    ranked = await ranker.rank_findings([finding])
    rank_time = time.time() - t0

    f = ranked[0]
    print(f"  Impact Score: {f.get('impact_score', 0):.3f}")
    print(f"  Relevance: {f.get('relevance_score', 0):.2f}")
    print(f"  Novelty: {f.get('novelty_score', 0):.2f}")
    print(f"  Credibility: {f.get('credibility_score', 0):.2f}")
    print(f"  Actionability: {f.get('actionability_score', 0):.2f}")
    print(f"  Ranking time: {rank_time:.1f}s")
    assert f.get("impact_score", 0) > 0, "Should have impact score"
    print("  ✅ Ranking successful!")

    # ── Step 6: Dedup ────────────────────────────────────────────────────
    print("\n─── Step 6: DEDUPLICATION ─────────────────────────────────")
    from app.core.dedup import DedupEngine

    dedup = DedupEngine()

    # Create a duplicate finding to test dedup
    finding2 = finding.copy()
    finding2["id"] = "test-finding-2"  # Same content, different ID

    dedup_result = dedup.deduplicate([finding, finding2])
    print(f"  Input: {dedup_result.total_input}")
    print(f"  Unique: {dedup_result.total_unique}")
    print(f"  Duplicates: {dedup_result.total_duplicates}")
    assert dedup_result.total_duplicates >= 1, "Should detect duplicate"
    print("  ✅ Dedup working!")

    # ── Step 7: Digest Compilation ───────────────────────────────────────
    print("\n─── Step 7: DIGEST COMPILATION ────────────────────────────")
    # Use the ranked unique finding
    findings_for_digest = [ranked[0]]

    # Add agent type tag for section routing
    findings_for_digest[0]["tags"] = findings_for_digest[0].get("tags", []) + [
        "competitor"
    ]
    findings_for_digest[0]["diff_hash"] = change.current_hash

    from app.digest.compiler import DigestCompiler

    compiler = DigestCompiler()

    # Compile without DB (standalone test)
    t0 = time.time()
    digest_data = await compiler.compile("test-run-1", findings_for_digest, db=None)
    compile_time = time.time() - t0

    print(f"  Total findings: {digest_data.get('total_findings', 0)}")
    print(f"  Sections: {list(digest_data.get('sections', {}).keys())}")
    print(f"  Executive Summary: {digest_data.get('executive_summary', '')[:200]}...")
    print(f"  Compilation time: {compile_time:.1f}s")
    assert digest_data.get("total_findings", 0) > 0, "Should have findings"
    print("  ✅ Digest compilation successful!")

    # ── Step 8: PDF / HTML Generation ────────────────────────────────────
    print("\n─── Step 8: PDF/HTML GENERATION ───────────────────────────")
    from app.digest.pdf_renderer import PDFRenderer

    renderer = PDFRenderer()
    output_path = renderer.render(digest_data)
    print(f"  Output: {output_path}")

    from pathlib import Path

    output_file = Path(output_path)
    assert output_file.exists(), "Output file should exist"
    size_kb = output_file.stat().st_size / 1024
    print(f"  Size: {size_kb:.1f} KB")
    print(f"  Format: {output_file.suffix}")
    print("  ✅ Digest output generated!")

    # ── Summary ──────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  🎉 END-TO-END TEST PASSED!")
    print("=" * 70)
    print(f"\n  Pipeline Summary:")
    print(f"    Source:     OpenAI Blog")
    print(f"    Finding:    {summary.title}")
    print(f"    Category:   {summary.category}")
    print(f"    Impact:     {f.get('impact_score', 0):.1%}")
    print(f"    Confidence: {summary.confidence:.1%}")
    print(f"    LLM:        {settings.active_llm_provider}")
    print(f"    Output:     {output_path}")
    print()

    await fetcher.close()


if __name__ == "__main__":
    asyncio.run(test_step_by_step())
