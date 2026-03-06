"""
Orchestrator - Run Manager for the full pipeline.

Manages the end-to-end daily run:
1. Set run status and agent status map
2. Launch selected agents in parallel
3. Compile digest and generate PDF
4. Send email (optional)
5. Persist digest and final run status
"""

import asyncio
from datetime import datetime, timezone
from typing import Optional

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
from app.models.run_agent_log import RunAgentLog
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

    async def execute_run(
        self,
        run_id: str,
        agent_types: Optional[list[str]] = None,
        source_ids: Optional[list[str]] = None,
        recipients_override: Optional[list[str]] = None,
        max_sources_per_agent: Optional[int] = None,
    ):
        """
        Execute a complete pipeline run.

        Optional filters allow cost-controlled/manual test runs.
        """
        logger.info("pipeline_run_start run_id=%s", run_id[:8])
        selected_agent_types = self._normalize_agent_types(agent_types)
        selected_source_ids = set(source_ids or [])
        recipients = self._normalize_recipients(recipients_override)

        async with async_session() as db:
            run = await self._get_run(run_id, db)
            if not run:
                logger.error("run_not_found run_id=%s", run_id)
                return

            run.status = RunStatus.RUNNING
            run.started_at = datetime.now(timezone.utc)
            run.agent_statuses = self._build_initial_agent_statuses(selected_agent_types)
            await db.commit()

            try:
                # Phase 1: Run selected agents
                all_findings = await self._run_agents(
                    run_id=run_id,
                    db=db,
                    selected_agent_types=selected_agent_types,
                    selected_source_ids=selected_source_ids or None,
                    max_sources_per_agent=max_sources_per_agent,
                )

                # Phase 2: Compile digest
                digest_data = await self.digest_compiler.compile(run_id, all_findings, db)

                # Phase 3: Generate PDF (always, even for zero-findings runs)
                pdf_path: Optional[str] = None
                try:
                    pdf_path = self.pdf_renderer.render(digest_data)
                except Exception as e:
                    logger.error("pdf_generation_error error=%s", str(e))

                # Phase 4: Send email (optional)
                email_sent = False
                effective_recipients = (
                    recipients if recipients is not None else settings.email_recipient_list
                )
                if pdf_path and effective_recipients and settings.has_email_configured:
                    try:
                        today = datetime.now().strftime("%Y-%m-%d")
                        subject = f"Zentivra AI Radar - {today}"
                        email_sent = await self.email_service.send_digest_email(
                            recipients=effective_recipients,
                            subject=subject,
                            executive_summary=digest_data.get("executive_summary", ""),
                            pdf_path=pdf_path,
                        )
                    except Exception as e:
                        logger.error("email_send_error error=%s", str(e))

                # Phase 5: Save digest record
                digest = Digest(
                    run_id=run_id,
                    date=datetime.now().date(),
                    executive_summary=digest_data.get("executive_summary", ""),
                    pdf_path=pdf_path,
                    email_sent=email_sent,
                    sent_at=datetime.now(timezone.utc) if email_sent else None,
                    recipients=effective_recipients if email_sent else None,
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

                # Phase 6: Finalize run status
                has_errors = any(
                    str(status).startswith("failed")
                    for status in (run.agent_statuses or {}).values()
                )
                run.status = RunStatus.PARTIAL if has_errors else RunStatus.COMPLETED
                run.completed_at = datetime.now(timezone.utc)
                run.total_findings = digest_data.get("total_findings", 0)
                run.error_log = None if run.status != RunStatus.PARTIAL else run.error_log

                await db.commit()

                logger.info(
                    "pipeline_run_complete run_id=%s status=%s findings=%d pdf=%s email=%s",
                    run_id[:8],
                    run.status,
                    run.total_findings,
                    bool(pdf_path),
                    email_sent,
                )

            except Exception as e:
                logger.error("pipeline_run_error run_id=%s error=%s", run_id[:8], str(e))
                run.status = RunStatus.FAILED
                run.error_log = str(e)
                run.completed_at = datetime.now(timezone.utc)
                await db.commit()

    async def _run_agents(
        self,
        run_id: str,
        db: AsyncSession,
        selected_agent_types: Optional[set[AgentType]] = None,
        selected_source_ids: Optional[set[str]] = None,
        max_sources_per_agent: Optional[int] = None,
    ) -> list[dict]:
        """Run agents in parallel and collect findings with partial-failure tolerance."""
        sources_by_type = await self._load_sources(
            db=db,
            selected_agent_types=selected_agent_types,
            selected_source_ids=selected_source_ids,
            max_sources_per_agent=max_sources_per_agent,
        )
        run = await self._get_run(run_id, db)

        tasks: list[asyncio.Task] = []

        for agent_type, agent_class in AGENT_MAP.items():
            if selected_agent_types and agent_type not in selected_agent_types:
                if run:
                    await self._set_agent_status(run, db, agent_type.value, "skipped (not selected)")
                continue

            sources = sources_by_type.get(agent_type, [])
            if not sources:
                logger.info("no_sources_for_agent agent_type=%s", agent_type.value)
                if run:
                    await self._set_agent_status(run, db, agent_type.value, "skipped (no sources)")
                continue

            if run:
                await self._set_agent_status(
                    run, db, agent_type.value, f"running ({len(sources)} sources)"
                )

            agent = agent_class()
            tasks.append(
                asyncio.create_task(
                    self._run_agent_job(
                        agent_name=agent_type.value,
                        agent_type=agent_type,
                        agent=agent,
                        run_id=run_id,
                        sources=sources,
                    )
                )
            )

        if not tasks:
            return []

        all_findings: list[dict] = []
        for task in asyncio.as_completed(tasks):
            agent_name, findings, error = await task
            if error:
                logger.error("agent_failed agent=%s error=%s", agent_name, str(error))
                if run:
                    await self._set_agent_status(
                        run,
                        db,
                        agent_name,
                        f"failed: {str(error)[:160]}",
                    )
                continue

            all_findings.extend(findings)
            if run:
                await self._set_agent_status(
                    run,
                    db,
                    agent_name,
                    f"completed ({len(findings)} findings)",
                )

        logger.info(
            "all_agents_complete total_findings=%d agents_run=%d",
            len(all_findings),
            len(tasks),
        )
        return all_findings

    async def _run_agent_job(
        self,
        agent_name: str,
        agent_type: AgentType,
        agent,
        run_id: str,
        sources: list[Source],
    ) -> tuple[str, list[dict], Optional[Exception]]:
        """Execute one agent task and return a normalized result tuple."""
        try:
            findings = await self._run_single_agent_with_timeout(
                agent=agent,
                run_id=run_id,
                sources=sources,
                agent_type=agent_type,
            )
            return agent_name, findings, None
        except Exception as e:
            return agent_name, [], e

    async def _run_single_agent_with_timeout(
        self,
        agent,
        run_id: str,
        sources: list[Source],
        agent_type: AgentType,
    ) -> list[dict]:
        """Run one agent with a hard timeout to prevent indefinite hangs."""
        timeout_seconds = max(0, int(settings.agent_timeout_seconds))
        if timeout_seconds == 0:
            return await self._run_single_agent(agent, run_id, sources, agent_type)

        try:
            return await asyncio.wait_for(
                self._run_single_agent(agent, run_id, sources, agent_type),
                timeout=timeout_seconds,
            )
        except asyncio.TimeoutError:
            async with async_session() as log_db:
                await self._append_agent_log(
                    db=log_db,
                    run_id=run_id,
                    agent_type=agent_type,
                    level="error",
                    message=f"agent_timeout timeout_seconds={timeout_seconds}",
                )
            raise RuntimeError(f"timed out after {timeout_seconds}s")

    async def _run_single_agent(
        self,
        agent,
        run_id: str,
        sources: list[Source],
        agent_type: AgentType,
    ) -> list[dict]:
        """Run a single agent with an isolated DB session."""
        async with async_session() as log_db:
            await self._append_agent_log(
                db=log_db,
                run_id=run_id,
                agent_type=agent_type,
                message=f"agent_started sources={len(sources)}",
                level="info",
            )

        try:
            async with async_session() as agent_db:
                async def _log_callback(
                    level: str,
                    message: str,
                    context: Optional[dict] = None,
                ) -> None:
                    async with async_session() as log_db:
                        await self._append_agent_log(
                            db=log_db,
                            run_id=run_id,
                            agent_type=agent_type,
                            level=level,
                            message=message,
                            context=context,
                        )

                findings = await agent.run(
                    run_id,
                    sources,
                    db=agent_db,
                    log_callback=_log_callback,
                )
                await agent_db.commit()
                return findings
        except Exception as e:
            async with async_session() as log_db:
                await self._append_agent_log(
                    db=log_db,
                    run_id=run_id,
                    agent_type=agent_type,
                    level="error",
                    message=f"agent_crashed error={str(e)[:300]}",
                )
            raise
        finally:
            await agent.close()

    async def _load_sources(
        self,
        db: AsyncSession,
        selected_agent_types: Optional[set[AgentType]] = None,
        selected_source_ids: Optional[set[str]] = None,
        max_sources_per_agent: Optional[int] = None,
    ) -> dict[AgentType, list[Source]]:
        """Load enabled sources grouped by agent type with optional filters."""
        query = select(Source).where(Source.enabled == True)  # noqa: E712

        if selected_agent_types:
            query = query.where(Source.agent_type.in_(list(selected_agent_types)))

        if selected_source_ids:
            query = query.where(Source.id.in_(list(selected_source_ids)))

        result = await db.execute(query)
        sources = result.scalars().all()

        grouped: dict[AgentType, list[Source]] = {}
        for source in sources:
            agent_type = AgentType(source.agent_type)
            grouped.setdefault(agent_type, []).append(source)

        if max_sources_per_agent:
            for key in list(grouped.keys()):
                grouped[key] = grouped[key][:max_sources_per_agent]

        return grouped

    async def _set_agent_status(
        self,
        run: Run,
        db: AsyncSession,
        agent_name: str,
        status: str,
    ) -> None:
        """Persist one agent status update reliably for JSON columns."""
        statuses = dict(run.agent_statuses or {})
        statuses[agent_name] = status
        run.agent_statuses = statuses
        await db.commit()

        agent_type = self._to_agent_type(agent_name)
        if agent_type:
            level = "error" if status.startswith("failed") else "info"
            async with async_session() as log_db:
                await self._append_agent_log(
                    db=log_db,
                    run_id=run.id,
                    agent_type=agent_type,
                    level=level,
                    message=f"status_update status={status}",
                    context={"status": status},
                )

    def _build_initial_agent_statuses(
        self, selected_agent_types: Optional[set[AgentType]]
    ) -> dict[str, str]:
        """Build the initial status map for all agents."""
        statuses: dict[str, str] = {}
        for agent_type in AGENT_MAP:
            if selected_agent_types and agent_type not in selected_agent_types:
                statuses[agent_type.value] = "skipped (not selected)"
            else:
                statuses[agent_type.value] = "pending"
        return statuses

    def _normalize_agent_types(
        self, agent_types: Optional[list[str]]
    ) -> Optional[set[AgentType]]:
        """Convert optional input strings to AgentType enums."""
        if not agent_types:
            return None

        normalized: set[AgentType] = set()
        for value in agent_types:
            try:
                normalized.add(AgentType(value))
            except ValueError:
                logger.warning("invalid_agent_type_filter value=%s", value)
        return normalized or None

    def _normalize_recipients(self, recipients: Optional[list[str]]) -> Optional[list[str]]:
        """Clean recipient overrides, returning None when no override is supplied."""
        if recipients is None:
            return None
        cleaned = [r.strip() for r in recipients if r and r.strip()]
        return cleaned

    async def _append_agent_log(
        self,
        db: AsyncSession,
        run_id: str,
        agent_type: AgentType,
        message: str,
        level: str = "info",
        context: Optional[dict] = None,
    ) -> None:
        """Persist one agent log line and commit for live UI visibility."""
        try:
            db.add(
                RunAgentLog(
                    run_id=run_id,
                    agent_type=agent_type,
                    level=level,
                    message=message,
                    context=context,
                )
            )
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.debug(
                "agent_log_persist_failed run_id=%s agent=%s error=%s",
                run_id[:8],
                agent_type.value,
                str(e),
            )

    def _to_agent_type(self, value: str) -> Optional[AgentType]:
        """Convert a string to AgentType safely."""
        try:
            return AgentType(value)
        except ValueError:
            return None

    async def _get_run(self, run_id: str, db: AsyncSession) -> Optional[Run]:
        """Get a run by ID."""
        result = await db.execute(select(Run).where(Run.id == run_id))
        return result.scalar_one_or_none()
