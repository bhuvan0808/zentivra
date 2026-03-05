"""
Orchestrator - Run Manager for the full pipeline.

Manages the end-to-end daily run:
1. Create a run record
2. Launch all 4 agents in parallel
3. Collect findings (partial failure tolerant)
4. Trigger digest compilation → PDF → email
5. Update run status
"""

import asyncio
from datetime import datetime, timezone
from typing import Optional

from app.utils.logger import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.competitor_watcher import CompetitorWatcher
from app.agents.hf_benchmark_tracker import HFBenchmarkTracker
from app.agents.model_provider_watcher import ModelProviderWatcher
from app.agents.research_scout import ResearchScout
from app.config import settings
from app.database import async_session
from app.digest.compiler import DigestCompiler
from app.digest.pdf_renderer import PDFRenderer
from app.models.digest import Digest
from app.models.run import Run, RunStatus
from app.models.source import AgentType, Source
from app.notifications.email_service import EmailService

from app.utils.logger import logger

# Agent type to agent class mapping
AGENT_MAP = {
    AgentType.COMPETITOR: CompetitorWatcher,
    AgentType.MODEL_PROVIDER: ModelProviderWatcher,
    AgentType.RESEARCH: ResearchScout,
    AgentType.HF_BENCHMARK: HFBenchmarkTracker,
}


class Orchestrator:
    """
    Pipeline orchestrator that manages the full daily run.

    Usage:
        orchestrator = Orchestrator()
        await orchestrator.execute_run(run_id)
    """

    def __init__(self):
        self.digest_compiler = DigestCompiler()
        self.pdf_renderer = PDFRenderer()
        self.email_service = EmailService()

    async def execute_run(self, run_id: str):
        """
        Execute a complete pipeline run.

        This is the main entry point called by the scheduler or manual trigger.
        """
        logger.info("pipeline_run_start run_id=%s", run_id[:8])

        async with async_session() as db:
            # Update run status to RUNNING
            run = await self._get_run(run_id, db)
            if not run:
                logger.error("run_not_found run_id=%s", run_id)
                return

            run.status = RunStatus.RUNNING
            run.started_at = datetime.now(timezone.utc)
            run.agent_statuses = {
                "competitor": "pending",
                "model_provider": "pending",
                "research": "pending",
                "hf_benchmark": "pending",
            }
            await db.commit()

            try:
                # ── Phase 1: Run all agents in parallel ──────────────────
                all_findings = await self._run_agents(run_id, db)

                # ── Phase 2: Compile digest ──────────────────────────────
                digest_data = await self.digest_compiler.compile(
                    run_id, all_findings, db
                )

                # ── Phase 3: Generate PDF ────────────────────────────────
                pdf_path = None
                if digest_data.get("total_findings", 0) > 0:
                    try:
                        pdf_path = self.pdf_renderer.render(digest_data)
                    except Exception as e:
                        logger.error("pdf_generation_error error=%s", str(e))

                # ── Phase 4: Send email ──────────────────────────────────
                email_sent = False
                recipients = settings.email_recipient_list
                if pdf_path and recipients and settings.has_email_configured:
                    try:
                        today = datetime.now().strftime("%Y-%m-%d")
                        subject = f"Zentivra AI Radar — {today}"
                        email_sent = await self.email_service.send_digest_email(
                            recipients=recipients,
                            subject=subject,
                            executive_summary=digest_data.get("executive_summary", ""),
                            pdf_path=pdf_path,
                        )
                    except Exception as e:
                        logger.error("email_send_error error=%s", str(e))

                # ── Phase 5: Save digest record ──────────────────────────
                digest = Digest(
                    run_id=run_id,
                    date=datetime.now().date(),
                    executive_summary=digest_data.get("executive_summary", ""),
                    pdf_path=pdf_path,
                    email_sent=email_sent,
                    sent_at=datetime.now(timezone.utc) if email_sent else None,
                    recipients=recipients if email_sent else None,
                    sections={
                        name: {
                            "count": data.get("count", 0),
                            "narrative": data.get("narrative", ""),
                        }
                        for name, data in digest_data.get("sections", {}).items()
                    },
                    total_findings=digest_data.get("total_findings", 0),
                )
                db.add(digest)

                # ── Phase 6: Update run status ───────────────────────────
                has_errors = any(
                    s == "failed"
                    for s in (run.agent_statuses or {}).values()
                )
                run.status = RunStatus.PARTIAL if has_errors else RunStatus.COMPLETED
                run.completed_at = datetime.now(timezone.utc)
                run.total_findings = digest_data.get("total_findings", 0)

                await db.commit()

                logger.info(
                    "pipeline_run_complete run_id=%s status=%s findings=%d pdf=%s email=%s",
                    run_id[:8],
                    run.status,
                    run.total_findings,
                    pdf_path is not None,
                    email_sent,
                )

            except Exception as e:
                logger.error("pipeline_run_error run_id=%s error=%s", run_id[:8], str(e))
                run.status = RunStatus.FAILED
                run.error_log = str(e)
                run.completed_at = datetime.now(timezone.utc)
                await db.commit()

    async def _run_agents(self, run_id: str, db: AsyncSession) -> list[dict]:
        """
        Run all 4 agents in parallel and collect findings.

        Partial failure tolerant: if one agent fails, the others continue.
        """
        # Load sources grouped by agent type
        sources_by_type = await self._load_sources(db)

        # Create agent tasks
        tasks = []
        agent_names = []

        for agent_type, agent_class in AGENT_MAP.items():
            sources = sources_by_type.get(agent_type, [])
            if not sources:
                logger.info("no_sources_for_agent", agent_type=agent_type.value)
                continue

            agent = agent_class()
            agent_names.append(agent_type.value)
            tasks.append(
                self._run_single_agent(agent, run_id, sources, db)
            )

        # Execute all agents in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect findings and update agent statuses
        all_findings = []
        run = await self._get_run(run_id, db)

        for i, result in enumerate(results):
            agent_name = agent_names[i] if i < len(agent_names) else f"agent_{i}"

            if isinstance(result, Exception):
                logger.error(
                    "agent_failed agent=%s error=%s",
                    agent_name,
                    str(result),
                )
                if run and run.agent_statuses:
                    run.agent_statuses[agent_name] = "failed"
            elif isinstance(result, list):
                all_findings.extend(result)
                if run and run.agent_statuses:
                    run.agent_statuses[agent_name] = f"completed ({len(result)} findings)"
            else:
                if run and run.agent_statuses:
                    run.agent_statuses[agent_name] = "completed (0 findings)"

        if run:
            await db.flush()

        logger.info(
            "all_agents_complete total_findings=%d agents_run=%d",
            len(all_findings),
            len(tasks),
        )

        return all_findings

    async def _run_single_agent(
        self,
        agent,
        run_id: str,
        sources: list[Source],
        db: AsyncSession,
    ) -> list[dict]:
        """Run a single agent with error handling."""
        try:
            findings = await agent.run(run_id, sources, db=db)
            return findings
        finally:
            await agent.close()

    async def _load_sources(self, db: AsyncSession) -> dict[AgentType, list[Source]]:
        """Load all enabled sources grouped by agent type."""
        result = await db.execute(
            select(Source).where(Source.enabled == True)
        )
        sources = result.scalars().all()

        grouped = {}
        for source in sources:
            agent_type = AgentType(source.agent_type)
            if agent_type not in grouped:
                grouped[agent_type] = []
            grouped[agent_type].append(source)

        return grouped

    async def _get_run(self, run_id: str, db: AsyncSession) -> Optional[Run]:
        """Get a run by ID."""
        result = await db.execute(select(Run).where(Run.id == run_id))
        return result.scalar_one_or_none()
