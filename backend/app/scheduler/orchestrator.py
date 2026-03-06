"""
Orchestrator - Run Manager for the full pipeline.

Manages the end-to-end daily run:
1. Create a run record
2. Launch all 4 agents in parallel
3. Collect findings (partial failure tolerant)
4. Trigger digest compilation -> PDF -> email
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
from app.config import settings, LOGS_DIR
from app.database import async_session
from app.digest.compiler import DigestCompiler
from app.digest.pdf_renderer import PDFRenderer
from app.models.digest import Digest
from app.models.run import Run, RunStatus
from app.models.source import AgentType, Source
from app.notifications.email_service import EmailService
from app.repositories.orchestrator_config_repository import OrchestratorConfigRepository
from app.schemas.orchestrator_config import OrchestratorConfigSchema
from app.services.orchestrator_config_service import OrchestratorConfigService
from app.utils.run_logger import RunLogger

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
        self.pdf_renderer = PDFRenderer()
        self.email_service = EmailService()

    async def _load_orchestrator_config(
        self, db, run_log: RunLogger
    ) -> OrchestratorConfigSchema:
        """Load the orchestrator config from DB (or defaults if none saved)."""
        try:
            repo = OrchestratorConfigRepository(db)
            svc = OrchestratorConfigService(repo)
            cfg = await svc.get_config_schema()
            run_log.info(
                "orchestrator_config_loaded",
                phase="init",
                llm_default=cfg.llm.default_provider,
                agents_configured=list(cfg.llm.agents.keys()),
            )
            return cfg
        except Exception as e:
            run_log.warning(
                "orchestrator_config_load_failed",
                phase="init",
                error=str(e),
            )
            return OrchestratorConfigSchema()

    async def execute_run(self, run_id: str):
        """
        Execute a complete pipeline run.

        This is the main entry point called by the scheduler or manual trigger.
        """
        run_log = RunLogger(run_id, LOGS_DIR)
        run_log.info("pipeline_run_start", phase="init")

        async with async_session() as db:
            run = await self._get_run(run_id, db)
            if not run:
                run_log.error("run_not_found", phase="init")
                run_log.close()
                return

            run.log_path = str(run_log.file_path)

            # Load orchestrator config from DB
            cfg = await self._load_orchestrator_config(db, run_log)

            # Validate LLM provider: use config default, fall back to env
            llm_provider = cfg.llm.default_provider or settings.active_llm_provider
            if llm_provider in ("none", ""):
                run_log.error(
                    "no_llm_provider_configured",
                    phase="init",
                    hint="Set a default_provider in config or set an LLM API key in .env",
                )
                run.status = RunStatus.FAILED
                run.error_log = "No LLM provider configured"
                run.completed_at = datetime.now(timezone.utc)
                await db.commit()
                run_log.close()
                return

            run_log.info(
                "llm_provider_active",
                phase="init",
                provider=llm_provider,
            )

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
                # -- Phase 1: Run all agents in parallel
                run_log.info("phase_start", phase="agents")
                all_findings = await self._run_agents(run_id, db, run_log, cfg)
                run_log.info(
                    "phase_complete",
                    phase="agents",
                    total_findings=len(all_findings),
                )

                # -- Phase 2: Compile digest (with config-driven dedup/ranking)
                run_log.info("phase_start", phase="digest")
                digest_compiler = DigestCompiler(
                    similarity_threshold=cfg.deduplication.similarity_threshold,
                    llm_provider=llm_provider,
                    llm_model=cfg.llm.default_model,
                    ranking_weights={
                        "relevance": cfg.ranking.relevance_weight,
                        "novelty": cfg.ranking.novelty_weight,
                        "credibility": cfg.ranking.credibility_weight,
                        "actionability": cfg.ranking.actionability_weight,
                    },
                )
                digest_data = await digest_compiler.compile(
                    run_id, all_findings, db
                )
                run_log.info(
                    "phase_complete",
                    phase="digest",
                    total_findings=digest_data.get("total_findings", 0),
                    duplicates_removed=digest_data.get("total_duplicates_removed", 0),
                )

                # -- Phase 3: Generate PDF
                pdf_path = None
                if digest_data.get("total_findings", 0) > 0:
                    try:
                        run_log.info("phase_start", phase="pdf")
                        pdf_path = self.pdf_renderer.render(digest_data)
                        run_log.info("phase_complete", phase="pdf", pdf_path=pdf_path)
                    except Exception as e:
                        run_log.error("pdf_generation_error", phase="pdf", error=str(e))

                # -- Phase 4: Send email
                email_sent = False
                recipients = (
                    cfg.notifications.email_recipients
                    or settings.email_recipient_list
                )
                if pdf_path and recipients and settings.has_email_configured:
                    try:
                        run_log.info(
                            "phase_start",
                            phase="email",
                            recipients=len(recipients),
                        )
                        today = datetime.now().strftime("%Y-%m-%d")
                        subject = f"Zentivra AI Radar — {today}"
                        email_sent = await self.email_service.send_digest_email(
                            recipients=recipients,
                            subject=subject,
                            executive_summary=digest_data.get("executive_summary", ""),
                            pdf_path=pdf_path,
                        )
                        run_log.info(
                            "phase_complete", phase="email", sent=email_sent
                        )
                    except Exception as e:
                        run_log.error("email_send_error", phase="email", error=str(e))

                # -- Phase 5: Save digest record
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

                # -- Phase 6: Update run status
                has_errors = any(
                    "failed" in str(s)
                    for s in (run.agent_statuses or {}).values()
                )
                run.status = RunStatus.PARTIAL if has_errors else RunStatus.COMPLETED
                run.completed_at = datetime.now(timezone.utc)
                run.total_findings = digest_data.get("total_findings", 0)

                await db.commit()

                run_log.info(
                    "pipeline_run_complete",
                    phase="done",
                    status=run.status.value,
                    findings=run.total_findings,
                    pdf=pdf_path is not None,
                    email=email_sent,
                )

            except Exception as e:
                run_log.error(
                    "pipeline_run_error", phase="fatal", error=str(e)
                )
                run.status = RunStatus.FAILED
                run.error_log = str(e)
                run.completed_at = datetime.now(timezone.utc)
                await db.commit()

            finally:
                run_log.close()

    async def _run_agents(
        self,
        run_id: str,
        db: AsyncSession,
        run_log: RunLogger,
        cfg: OrchestratorConfigSchema,
    ) -> list[dict]:
        """
        Run all 4 agents in parallel and collect findings.

        Partial failure tolerant: if one agent fails, the others continue.
        """
        sources_by_type = await self._load_sources(db)

        tasks = []
        agent_names = []

        for agent_type, agent_class in AGENT_MAP.items():
            sources = sources_by_type.get(agent_type, [])
            if not sources:
                run_log.info(
                    "no_sources_for_agent",
                    phase="agents",
                    agent=agent_type.value,
                )
                continue

            # Resolve per-agent LLM config from DB config
            agent_key = agent_type.value
            agent_llm = cfg.llm.agents.get(agent_key)
            llm_provider = agent_llm.provider if agent_llm else cfg.llm.default_provider
            llm_model = agent_llm.model if agent_llm else cfg.llm.default_model

            agent = agent_class(llm_provider=llm_provider, llm_model=llm_model)
            agent_names.append(agent_key)
            tasks.append(
                self._run_single_agent(agent, run_id, sources, db, run_log)
            )

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_findings = []
        run = await self._get_run(run_id, db)

        for i, result in enumerate(results):
            agent_name = agent_names[i] if i < len(agent_names) else f"agent_{i}"

            if isinstance(result, Exception):
                run_log.error(
                    "agent_failed",
                    phase="agents",
                    agent=agent_name,
                    error=str(result),
                )
                if run and run.agent_statuses:
                    run.agent_statuses[agent_name] = f"failed: {str(result)[:120]}"
            elif isinstance(result, list):
                all_findings.extend(result)
                if run and run.agent_statuses:
                    run.agent_statuses[agent_name] = (
                        f"completed ({len(result)} findings)"
                    )
            else:
                if run and run.agent_statuses:
                    run.agent_statuses[agent_name] = "completed (0 findings)"

        if run:
            await db.flush()

        run_log.info(
            "all_agents_complete",
            phase="agents",
            total_findings=len(all_findings),
            agents_run=len(tasks),
        )

        return all_findings

    async def _run_single_agent(
        self,
        agent,
        run_id: str,
        sources: list[Source],
        db: AsyncSession,
        run_log: RunLogger,
    ) -> list[dict]:
        """Run a single agent with error handling."""
        try:
            findings = await agent.run(run_id, sources, db=db, run_logger=run_log)
            return findings
        finally:
            await agent.close()

    async def _load_sources(self, db: AsyncSession) -> dict[AgentType, list[Source]]:
        """Load all enabled sources grouped by agent type."""
        result = await db.execute(select(Source).where(Source.enabled == True))
        sources = result.scalars().all()

        grouped: dict[AgentType, list[Source]] = {}
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
