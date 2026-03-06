"""
Quality Tests — Guardrails and validation checks.

Ensures the system produces reliable, accurate output:
- LLM response parsing handles malformed JSON
- Summarizer guardrails work (confidence bounds, content length)
- Agent type inference is accurate
- Config validation catches misconfigurations
"""

import sys
import json
import pytest

sys.path.insert(0, ".")


class TestSummarizerGuardrails:
    """Test LLM output parsing and guardrails."""

    def setup_method(self):
        from app.core.summarizer import Summarizer

        self.summarizer = Summarizer()

    def test_parse_clean_json(self):
        """Should parse valid JSON response."""
        response = json.dumps(
            {
                "title": "Test Finding",
                "summary_short": "A test summary",
                "confidence": 0.8,
                "category": "models",
                "tags": ["test"],
                "entities": {"companies": ["OpenAI"]},
            }
        )
        result = self.summarizer._parse_json_response(response)
        assert result["title"] == "Test Finding"
        assert result["confidence"] == 0.8

    def test_parse_markdown_wrapped_json(self):
        """Should handle JSON wrapped in markdown code blocks."""
        response = '```json\n{"title": "Test", "confidence": 0.7}\n```'
        result = self.summarizer._parse_json_response(response)
        assert result["title"] == "Test"

    def test_parse_json_with_extra_text(self):
        """Should extract JSON from responses with extra text."""
        response = 'Here is the analysis:\n\n{"title": "Found", "category": "models"}\n\nHope this helps!'
        result = self.summarizer._parse_json_response(response)
        assert result["title"] == "Found"

    def test_parse_malformed_json(self):
        """Should return empty dict for completely malformed input."""
        result = self.summarizer._parse_json_response("This is not JSON at all")
        assert result == {}

    def test_summary_result_defaults(self):
        """SummaryResult should have safe defaults."""
        from app.core.summarizer import SummaryResult

        result = SummaryResult()
        assert result.confidence == 0.5
        assert result.category == "other"
        assert result.tags == []
        assert result.success is True

    def test_parse_summary_missing_fields(self):
        """Should handle partial JSON gracefully."""
        response = json.dumps({"title": "Partial", "category": "apis"})
        result = self.summarizer._parse_summary_response(response)
        assert result.title == "Partial"
        assert result.category == "apis"
        assert result.confidence == 0.5  # Default

    def test_short_content_rejection(self):
        """Content < 50 chars should be rejected."""
        import asyncio

        result = asyncio.run(self.summarizer.summarize("Too short"))
        assert result.success is False
        assert result.confidence == 0.0


class TestAgentTypeInference:
    """Test that the digest compiler correctly routes findings to sections."""

    def setup_method(self):
        from app.digest.compiler import DigestCompiler

        self.compiler = DigestCompiler()

    def test_research_inference(self):
        """Research papers should route to research section."""
        finding = {"tags": ["research_paper"], "category": "research"}
        assert self.compiler._infer_agent_type(finding) == "research"

    def test_benchmark_inference(self):
        """Benchmark results should route to hf_benchmark."""
        finding = {"tags": ["benchmark_result"], "category": "benchmarks"}
        assert self.compiler._infer_agent_type(finding) == "hf_benchmark"

    def test_sota_inference(self):
        """SOTA claims should route to hf_benchmark."""
        finding = {"tags": ["sota_claim"], "category": "models"}
        assert self.compiler._infer_agent_type(finding) == "hf_benchmark"

    def test_model_provider_inference(self):
        """Model releases should route to model_provider."""
        finding = {"tags": ["model_release"], "category": "models"}
        assert self.compiler._infer_agent_type(finding) == "model_provider"

    def test_default_inference(self):
        """Unknown items should default to competitor."""
        finding = {"tags": [], "category": "other"}
        assert self.compiler._infer_agent_type(finding) == "competitor"


class TestEmailService:
    """Test email service validation."""

    def test_no_recipients_returns_false(self):
        """Should return False with no recipients."""
        import asyncio
        from app.notifications.email_service import EmailService

        service = EmailService()
        result = asyncio.run(
            service.send_digest_email(
                recipients=[],
                subject="Test",
                executive_summary="Test",
            )
        )
        assert result is False

    def test_email_body_generation(self):
        """Should generate valid HTML email body."""
        from app.notifications.email_service import EmailService

        service = EmailService()
        body = service._build_email_body(
            executive_summary="Today's key AI developments include a model launch.",
            dashboard_url="http://localhost:3000",
            pdf_path="/tmp/test.pdf",
        )
        assert "ZENTIVRA" in body
        assert "Executive Summary" in body
        assert "localhost:3000" in body


class TestScheduler:
    """Test scheduler configuration."""

    def test_scheduler_status_when_not_running(self):
        """Should report not running when scheduler hasn't started."""
        from app.scheduler.scheduler import get_scheduler_status

        status = get_scheduler_status()
        assert status["running"] is False

    def test_manual_trigger_import(self):
        """Manual trigger function should be importable."""
        from app.scheduler.scheduler import manual_trigger

        assert callable(manual_trigger)

    def test_orchestrator_imports(self):
        """Orchestrator should import and instantiate."""
        from app.scheduler.orchestrator import Orchestrator

        orc = Orchestrator()
        assert orc.digest_compiler is not None
        assert orc.pdf_renderer is not None
        assert orc.email_service is not None


class TestConfigValidation:
    """Test configuration edge cases."""

    def test_placeholder_keys_not_detected(self):
        """Placeholder API keys should NOT activate providers."""
        from app.config import Settings

        s = Settings(
            gemini_api_key="your-gemini-api-key-here",
            openai_api_key="your-openai-api-key-here",
        )
        assert s.active_llm_provider in (
            "groq",
            "openrouter",
            "none",
        ) or s.active_llm_provider not in ("gemini", "openai")

    def test_digest_dir_exists(self):
        """Data directories should exist."""
        from app.config import DIGESTS_DIR, SNAPSHOTS_DIR

        assert DIGESTS_DIR.exists()
        assert SNAPSHOTS_DIR.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
