"""Service layer for one-off workflows."""

import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.agents.competitor_watcher import CompetitorWatcher
from app.agents.hf_benchmark_tracker import HFBenchmarkTracker
from app.agents.model_provider_watcher import ModelProviderWatcher
from app.agents.research_scout import ResearchScout
from app.config import DIGESTS_DIR, settings
from app.digest.compiler import DigestCompiler
from app.digest.pdf_renderer import PDFRenderer
from app.models.source import AgentType, Source
from app.notifications.email_service import EmailService
from app.utils.logger import logger

AGENT_MAP = {
    AgentType.COMPETITOR: CompetitorWatcher,
    AgentType.MODEL_PROVIDER: ModelProviderWatcher,
    AgentType.RESEARCH: ResearchScout,
    AgentType.HF_BENCHMARK: HFBenchmarkTracker,
}


class WorkflowService:
    """Business logic for non-scheduled/ad-hoc workflows."""

    def __init__(self):
        self.digest_compiler = DigestCompiler()
        self.pdf_renderer = PDFRenderer()
        self.email_service = EmailService()

    async def disruptive_article_report(
        self,
        url: str,
        recipient_email: str,
        agent_types: Optional[list[AgentType]] = None,
        title: Optional[str] = None,
    ) -> dict:
        """
        Generate a one-off report for a disruptive article URL and email it.

        This flow does not persist to core tables; it is a rapid ad-hoc analysis path.
        """
        if not url.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")

        selected_agents = agent_types or list(AGENT_MAP.keys())
        report_id = str(uuid.uuid4())

        tasks = [
            self._run_single_agent_on_url(report_id, agent_type, url)
            for agent_type in selected_agents
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        findings: list[dict] = []
        for idx, result in enumerate(results):
            agent_type = selected_agents[idx]
            if isinstance(result, Exception):
                logger.error(
                    "adhoc_agent_failed agent=%s error=%s",
                    agent_type.value,
                    str(result),
                )
                continue
            findings.extend(result)

        digest_data = await self.digest_compiler.compile(report_id, findings, db=None)

        if title:
            digest_data["executive_summary"] = (
                f"{title}\n\n{digest_data.get('executive_summary', '')}"
            ).strip()

        pdf_path = self.pdf_renderer.render(digest_data)
        pdf_path = self._normalize_disruptive_pdf_name(report_id, pdf_path)
        subject_date = datetime.now().strftime("%Y-%m-%d")
        subject = f"Zentivra Disruptive Article Report - {subject_date}"
        email_sent = await self.email_service.send_digest_email(
            recipients=[recipient_email],
            subject=subject,
            executive_summary=digest_data.get("executive_summary", ""),
            pdf_path=pdf_path,
        )

        return {
            "report_id": report_id,
            "findings_count": digest_data.get("total_findings", 0),
            "email_sent": email_sent,
            "pdf_path": pdf_path,
            "agents_used": selected_agents,
        }

    def get_disruptive_report_pdf_path(self, report_id: str) -> Path:
        """Resolve the generated disruptive report PDF path by report ID."""
        return DIGESTS_DIR / f"disruptive_article_{report_id}.pdf"

    def _normalize_disruptive_pdf_name(self, report_id: str, raw_path: str) -> str:
        """Rename generated report to a deterministic file name for download APIs."""
        source = Path(raw_path)
        if not source.exists() or source.suffix.lower() != ".pdf":
            return raw_path

        target = self.get_disruptive_report_pdf_path(report_id)
        if source.resolve() == target.resolve():
            return str(target)

        source.replace(target)
        return str(target)

    async def _run_single_agent_on_url(
        self,
        report_id: str,
        agent_type: AgentType,
        url: str,
    ) -> list[dict]:
        """Run one agent against a single explicit URL."""
        agent_class = AGENT_MAP[agent_type]
        agent = agent_class()
        try:
            synthetic_source = Source(
                id=str(uuid.uuid4()),
                agent_type=agent_type,
                name=f"AdHoc {agent_type.value}",
                url=url,
                feed_url=None,
                css_selectors=None,
                keywords=None,
                rate_limit_rpm=settings.default_rate_limit_rpm,
                crawl_depth=1,
                enabled=True,
            )
            return await agent.run(report_id, [synthetic_source], db=None)
        finally:
            await agent.close()
