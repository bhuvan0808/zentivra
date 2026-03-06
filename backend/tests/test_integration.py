"""
Integration Tests — Full pipeline flow tests.

Tests the pipeline components working together, including
database operations and the orchestrator logic.
"""

import sys
import asyncio
import pytest

sys.path.insert(0, ".")


class TestPipelineIntegration:
    """Test components working together in the pipeline."""

    def test_fetch_and_extract(self):
        """Fetch a page and extract content."""
        from app.core.fetcher import Fetcher
        from app.core.extractor import Extractor

        async def run():
            fetcher = Fetcher()
            try:
                result = await fetcher.fetch(
                    "https://example.com",
                    rate_limit_rpm=30,
                    use_playwright_fallback=False,
                )
                assert result.success, f"Fetch failed: {result.error}"

                extractor = Extractor()
                extraction = extractor.extract_html(result.content)
                assert extraction.text, "Should extract text from example.com"
                return True
            finally:
                await fetcher.close()

        assert asyncio.run(run()) is True

    def test_extract_then_change_detect(self):
        """Extract content, then run through change detector."""
        from app.core.extractor import Extractor
        from app.core.change_detector import ChangeDetector

        html = """
        <html><body>
        <article><h1>Test</h1><p>Important AI news content here.</p></article>
        </body></html>
        """

        extractor = Extractor()
        extraction = extractor.extract_html(html)

        detector = ChangeDetector()
        # First detection
        change1 = detector.compare(None, extraction.text)
        assert change1.has_changed is True

        # Same content again
        change2 = detector.compare(extraction.text, extraction.text)
        assert change2.has_changed is False

    def test_dedup_then_rank(self):
        """Deduplicate findings, then rank them."""
        from app.core.dedup import DedupEngine
        from app.core.ranker import Ranker

        findings = [
            {
                "id": "1",
                "title": "Major Release",
                "summary_short": "Big news",
                "diff_hash": "hash_a",
                "category": "models",
                "confidence": 0.9,
                "tags": [],
                "entities": {},
            },
            {
                "id": "2",
                "title": "Minor Update",
                "summary_short": "Small change",
                "diff_hash": "hash_b",
                "category": "other",
                "confidence": 0.3,
                "tags": [],
                "entities": {},
            },
            {
                "id": "3",
                "title": "Major Release",
                "summary_short": "Big news",
                "diff_hash": "hash_a",
                "category": "models",
                "confidence": 0.9,
                "tags": [],
                "entities": {},
            },
        ]

        # Dedup
        dedup = DedupEngine()
        result = dedup.deduplicate(findings)
        assert result.total_unique == 2
        assert result.total_duplicates == 1

        # Rank
        ranker = Ranker(use_llm=False)
        ranked = asyncio.run(ranker.rank_findings(result.unique_findings))
        assert len(ranked) == 2
        # Higher confidence models should rank first
        assert ranked[0]["title"] == "Major Release"

    def test_digest_compilation_flow(self):
        """Test the full compilation: dedup -> rank -> compile -> render."""
        from app.digest.compiler import DigestCompiler
        from app.digest.pdf_renderer import PDFRenderer

        findings = [
            {
                "id": "1",
                "run_id": "test",
                "source_id": "src1",
                "title": "GPT-5 Released",
                "summary_short": "Major model update",
                "summary_long": "Detailed description of GPT-5.",
                "why_it_matters": "Significant impact on industry.",
                "category": "models",
                "confidence": 0.9,
                "tags": ["model_release"],
                "entities": {"companies": ["OpenAI"]},
                "source_url": "https://openai.com",
                "publisher": "OpenAI",
                "diff_hash": "hash_1",
            },
        ]

        compiler = DigestCompiler()
        digest = asyncio.run(compiler.compile("test-run", findings, db=None))

        assert digest["total_findings"] >= 1
        assert digest["executive_summary"]

        # Render to HTML
        renderer = PDFRenderer()
        html = renderer.render_html_only(digest)
        assert "ZENTIVRA" in html
        assert "GPT-5" in html or "gpt" in html.lower()


class TestDatabaseModels:
    """Test database model creation and relationships."""

    def test_source_model_creation(self):
        """Source model should be importable and instantiable."""
        from app.models.source import Source, AgentType

        source = Source(
            agent_type=AgentType.COMPETITOR,
            name="Test Source",
            url="https://example.com",
            enabled=True,
        )
        assert source.name == "Test Source"
        assert source.agent_type == AgentType.COMPETITOR
        assert source.enabled is True

    def test_finding_model_creation(self):
        """Finding model should handle all fields."""
        from app.models.finding import Finding

        finding = Finding(
            run_id="test-run",
            source_id="test-source",
            title="Test Finding",
            category="models",
            confidence=0.85,
            impact_score=0.75,
        )
        assert finding.title == "Test Finding"
        assert finding.confidence == 0.85

    def test_run_model_creation(self):
        """Run model should have correct defaults."""
        from app.models.run import Run, RunStatus

        run = Run(triggered_by="manual", status=RunStatus.PENDING)
        assert run.triggered_by == "manual"
        assert run.status == RunStatus.PENDING

    def test_digest_model_creation(self):
        """Digest model should be instantiable."""
        from app.models.digest import Digest
        from datetime import date

        digest = Digest(
            run_id="test-run",
            date=date.today(),
            executive_summary="Test summary",
            total_findings=5,
        )
        assert digest.total_findings == 5


class TestAPISchemas:
    """Test Pydantic schemas for validation."""

    def test_source_schema(self):
        """Source response schema should validate."""
        from app.schemas.source import SourceResponse

        # Test that schema fields exist
        assert "id" in SourceResponse.model_fields
        assert "name" in SourceResponse.model_fields
        assert "url" in SourceResponse.model_fields

    def test_run_schema(self):
        """Run response schema should validate."""
        from app.schemas.run import RunResponse

        assert "id" in RunResponse.model_fields
        assert "status" in RunResponse.model_fields

    def test_finding_schema(self):
        """Finding response schema should validate."""
        from app.schemas.finding import FindingResponse

        assert "id" in FindingResponse.model_fields
        assert "title" in FindingResponse.model_fields
        assert "impact_score" in FindingResponse.model_fields


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
