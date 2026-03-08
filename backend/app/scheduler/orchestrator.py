"""
Orchestrator - Central coordinator for the full pipeline execution.

Coordinates the entire pipeline for a triggered run. Key flow:

1. Resolve sources for the run - Map source UUIDs from Run config to Source
   objects, grouped by agent type.

2. Run agents in parallel - Each agent processes its sources via BFS crawl ->
   fetch -> extract -> preprocess -> summarize. Agents run concurrently.

3. Consume structured agent results - Collect findings, errors, urls_attempted,
   urls_succeeded from each agent. Determine per-agent status (completed,
   completed_empty, partial, failed).

4. Persist findings to DB - Write Finding records for all extracted findings.

5. Create snapshots per source - Per-source execution summary records in DB.

6. Determine trigger status - Aggregate agent outcomes into final status:
   completed, completed_empty, partial, or failed.

7. Conditional PDF/HTML digest generation - Only when run enables it and
   status is not failed/completed_empty and findings exist.

8. Conditional email notification - Best-effort send when email is enabled
   and digest PDF was generated.

Error handling strategy:
- On source resolution failure: immediate DB commit, status=failed, return.
- On finding persistence failure: immediate DB commit, status=failed, return.
- On snapshot creation failure: log only, continue (non-fatal).
- On digest generation failure when status would be completed: downgrade to
  partial, commit.
- On any uncaught exception in execute(): status=failed, attempt commit,
  log commit failure if it occurs.

Execution state lives on RunTrigger, NOT on Run (which is pure config).
"""

import asyncio
from datetime import datetime, timezone
from pathlib import Path
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
from app.models.digest_snapshot import DigestSnapshot
from app.models.finding import Finding
from app.models.run import Run
from app.models.run_trigger import RunTrigger
from app.models.snapshot import Snapshot
from app.models.source import AgentType, Source
from app.notifications.email_service import EmailService
from app.utils.logger import logger
from app.utils.run_logger import RunLogger

AGENT_MAP = {
    AgentType.COMPETITOR: CompetitorWatcher,
    AgentType.MODEL_PROVIDER: ModelProviderWatcher,
    AgentType.RESEARCH: ResearchScout,
    AgentType.HF_BENCHMARK: HFBenchmarkTracker,
}

# Resolved log directory (relative to backend/)
LOG_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "logs"


class Orchestrator:
    """
    Central orchestrator that coordinates the full pipeline execution.

    Manages source resolution, parallel agent execution, finding persistence,
    snapshot creation, digest generation, and email notification. Uses
    immediate DB commits on failure to ensure trigger status is persisted.
    """

    def __init__(self):
        self.digest_compiler = DigestCompiler()
        self.pdf_renderer = PDFRenderer()
        self.email_service = EmailService()

    async def execute(
        self,
        run_trigger_id: int,
        run_id: int,
        options: dict | None = None,
    ):
        """
        Entry point for pipeline execution, called by the background task.

        Error handling: On source resolution or finding persistence failure,
        status is set to "failed" and committed immediately before returning.
        On uncaught exception, status is set to "failed" and commit is attempted.
        """
        opts = options or {}
        logger.info(
            "pipeline_start run_trigger_id=%s run_id=%s", run_trigger_id, run_id
        )

        async with async_session() as db:
            trigger = await db.get(RunTrigger, run_trigger_id)
            run = await db.get(Run, run_id)

            if not trigger or not run:
                logger.error(
                    "pipeline_abort trigger=%s run=%s",
                    run_trigger_id,
                    run_id,
                )
                return

            # ── Initialise per-trigger run logger ───────────────
            run_log = RunLogger(trigger.run_trigger_id, LOG_DIR)
            run_log.info(
                "pipeline_start",
                step="pipeline",
                run_trigger_id=trigger.run_trigger_id,
                run_id=run.run_id,
            )

            # ── Capture user_id from the run for downstream records ─
            run_user_id: int = run.user_id

            # ── Mark running ────────────────────────────────────
            trigger.status = "running"
            await db.commit()
            run_log.info("status_changed", step="pipeline", status="running")

            try:
                # ── 1. Source resolution ────────────────────────────
                # Resolve source UUIDs from run config -> grouped Source objects.
                try:
                    sources_by_type = await self._resolve_sources(run, db, opts)
                except Exception as exc:
                    logger.error("source_resolution_error err=%s", str(exc)[:300])
                    run_log.error(
                        "source_resolution_error",
                        step="source_resolution",
                        error=str(exc)[:300],
                    )
                    trigger.status = "failed"
                    await db.commit()
                    run_log.info("status_changed", step="pipeline", status="failed")
                    run_log.close()
                    return

                total_source_count = sum(len(v) for v in sources_by_type.values())
                logger.info(
                    "sources_resolved types=%d total_sources=%d",
                    len(sources_by_type),
                    total_source_count,
                )
                run_log.info(
                    "sources_resolved",
                    step="source_resolution",
                    agent_types=len(sources_by_type),
                    total_sources=total_source_count,
                )

                if not sources_by_type:
                    trigger.status = "completed_empty"
                    await db.commit()
                    run_log.info(
                        "pipeline_complete_no_sources",
                        step="pipeline",
                        status="completed_empty",
                    )
                    logger.info("pipeline_complete_no_sources")
                    run_log.close()
                    return

                # ── 2. Parallel agent execution ─────────────────────
                # Each agent: BFS crawl -> fetch -> extract -> preprocess -> summarize.
                run_log.info(
                    "agents_starting",
                    step="pipeline",
                    agent_count=len(sources_by_type),
                )
                agent_results = await self._run_agents_parallel(
                    sources_by_type=sources_by_type,
                    run_config=run,
                    run_log=run_log,
                )

                # ── 3. Consume structured agent results ─────────────
                # Collect findings, errors, urls_attempted, urls_succeeded; derive agent status.
                all_finding_dicts: list[dict] = []
                agent_statuses: dict[str, str] = {}

                for agent_name, result, error in agent_results:
                    if error:
                        logger.error(
                            "agent_failed agent=%s err=%s",
                            agent_name,
                            str(error)[:300],
                        )
                        run_log.info(
                            "agent_failed",
                            step="pipeline",
                            agent=agent_name,
                            error=str(error)[:300],
                        )
                        agent_statuses[agent_name] = "failed"
                        continue

                    findings = result.get("findings", [])
                    errors = result.get("errors", [])
                    attempted = result.get("urls_attempted", 0)
                    succeeded = result.get("urls_succeeded", 0)

                    if attempted == 0:
                        agent_statuses[agent_name] = "completed_empty"
                    elif succeeded == 0 and errors:
                        agent_statuses[agent_name] = "failed"
                    elif errors:
                        agent_statuses[agent_name] = "partial"
                    else:
                        agent_statuses[agent_name] = "completed"

                    all_finding_dicts.extend(findings)

                    run_log.info(
                        "agent_result",
                        step="pipeline",
                        agent=agent_name,
                        status=agent_statuses[agent_name],
                        findings=len(findings),
                        errors=len(errors),
                    )

                    if errors:
                        logger.warning(
                            "agent_errors agent=%s count=%d first=%s",
                            agent_name,
                            len(errors),
                            errors[0][:200],
                        )

                # ── 4. Finding persistence ──────────────────────────
                # Write Finding records to DB. On failure: immediate commit, status=failed.
                try:
                    await self._persist_findings(
                        all_finding_dicts,
                        trigger.id,
                        run_user_id,
                        db,
                    )
                    run_log.info(
                        "findings_persisted",
                        step="finding_persist",
                        count=len(all_finding_dicts),
                    )
                except Exception as exc:
                    logger.error(
                        "finding_persistence_error err=%s",
                        str(exc)[:300],
                    )
                    run_log.error(
                        "finding_persistence_error",
                        step="finding_persist",
                        error=str(exc)[:300],
                    )
                    trigger.status = "failed"
                    await db.commit()
                    run_log.info("status_changed", step="pipeline", status="failed")
                    run_log.close()
                    return

                # ── 5. Snapshot generation ──────────────────────────
                # Create per-source Snapshot records. Non-fatal on failure.
                snapshot_ids: list[int] = []
                try:
                    snapshot_ids = await self._create_snapshots(
                        sources_by_type,
                        all_finding_dicts,
                        agent_statuses,
                        trigger.id,
                        db,
                    )
                    run_log.info(
                        "snapshots_created",
                        step="snapshot_create",
                        count=len(snapshot_ids),
                    )
                except Exception as exc:
                    logger.error(
                        "snapshot_creation_error err=%s",
                        str(exc)[:300],
                    )
                    run_log.error(
                        "snapshot_creation_error",
                        step="snapshot_create",
                        error=str(exc)[:300],
                    )

                # ── 6. Determine trigger status from agent outcomes ─
                # completed | completed_empty | partial | failed.
                statuses = set(agent_statuses.values())

                if all(s == "failed" for s in agent_statuses.values()):
                    trigger.status = "failed"
                elif "failed" in statuses or "partial" in statuses:
                    trigger.status = "partial"
                elif not all_finding_dicts:
                    trigger.status = "completed_empty"
                else:
                    trigger.status = "completed"

                await db.commit()
                run_log.info(
                    "status_changed",
                    step="pipeline",
                    status=trigger.status,
                )

                logger.info(
                    "agents_done status=%s findings=%d agent_statuses=%s",
                    trigger.status,
                    len(all_finding_dicts),
                    agent_statuses,
                )

                # ── 7. Conditional PDF / HTML ───────────────────────
                # Only when enable_pdf_gen, status not failed/completed_empty, and findings exist.
                digest_record = None
                if (
                    run.enable_pdf_gen
                    and trigger.status not in ("failed", "completed_empty")
                    and all_finding_dicts
                ):
                    run_log.info("digest_generation_start", step="digest_compile")
                    digest_record = await self._generate_digest(
                        trigger,
                        run,
                        all_finding_dicts,
                        snapshot_ids,
                        run_user_id,
                        db,
                    )
                    if digest_record:
                        run_log.info(
                            "digest_generated",
                            step="digest_compile",
                            digest_id=digest_record.digest_id[:8],
                            has_pdf=bool(digest_record.pdf_path),
                        )
                    else:
                        run_log.warning(
                            "digest_generation_failed",
                            step="digest_compile",
                        )
                    if digest_record is None and trigger.status == "completed":
                        trigger.status = "partial"
                        await db.commit()

                # ── 8. Conditional email (best-effort, log only) ────
                # When enable_email_alert, email configured, and digest PDF exists.
                if (
                    run.enable_email_alert
                    and settings.has_email_configured
                    and digest_record
                    and digest_record.pdf_path
                ):
                    recipients = (
                        run.email_recipients
                        or opts.get("recipients")
                        or settings.email_recipient_list
                    )
                    run_log.info(
                        "email_sending",
                        step="email_send",
                        recipients=len(recipients),
                    )
                    await self._send_email(
                        digest_record,
                        recipients,
                    )
                    run_log.info("email_sent", step="email_send")

                await db.commit()

                run_log.info(
                    "pipeline_complete",
                    step="pipeline",
                    status=trigger.status,
                    findings=len(all_finding_dicts),
                    has_pdf=bool(digest_record and digest_record.pdf_path),
                    email_enabled=run.enable_email_alert,
                )

                logger.info(
                    "pipeline_complete trigger=%s status=%s findings=%d pdf=%s email=%s",
                    trigger.run_trigger_id[:8],
                    trigger.status,
                    len(all_finding_dicts),
                    bool(digest_record and digest_record.pdf_path),
                    run.enable_email_alert,
                )

            except Exception as exc:
                logger.error(
                    "pipeline_error trigger=%s err=%s",
                    trigger.run_trigger_id[:8],
                    str(exc)[:500],
                )
                run_log.error(
                    "pipeline_error",
                    step="pipeline",
                    error=str(exc)[:500],
                )
                trigger.status = "failed"
                try:
                    await db.commit()
                except Exception as commit_exc:
                    logger.error(
                        "pipeline_final_commit_failed err=%s",
                        str(commit_exc)[:200],
                    )
            finally:
                run_log.close()

    # ── Layer 1: Source Resolution ──────────────────────────────────

    async def _resolve_sources(
        self,
        run: Run,
        db: AsyncSession,
        opts: dict,
    ) -> dict[str, list[Source]]:
        """Resolve source UUIDs from run config -> grouped Source objects."""
        source_uuids: list[str] = run.sources or []
        if not source_uuids:
            return {}

        result = await db.execute(
            select(Source).where(
                Source.source_id.in_(source_uuids), Source.is_enabled == True
            )  # noqa: E712
        )
        sources = list(result.scalars().all())

        max_per_agent = opts.get("max_sources_per_agent")
        grouped: dict[str, list[Source]] = {}
        for source in sources:
            grouped.setdefault(source.agent_type, []).append(source)

        if max_per_agent:
            for key in list(grouped.keys()):
                grouped[key] = grouped[key][:max_per_agent]

        return grouped

    # ── Layer 2: Parallel Agent Execution ──────────────────────────

    # Sentinel returned when an agent times out or raises; provides valid structure
    # (findings, errors, urls_attempted, urls_succeeded) so consumers need no special-case.
    _EMPTY_AGENT_RESULT: dict = {
        "findings": [],
        "errors": [],
        "urls_attempted": 0,
        "urls_succeeded": 0,
    }

    async def _run_agents_parallel(
        self,
        sources_by_type: dict[str, list[Source]],
        run_config: Run,
        run_log: RunLogger | None = None,
    ) -> list[tuple[str, dict, Optional[Exception]]]:
        """Run all agent types concurrently, returning structured results."""
        tasks: list[asyncio.Task] = []

        for agent_type_str, sources in sources_by_type.items():
            try:
                agent_type = AgentType(agent_type_str)
            except ValueError:
                logger.warning("unknown_agent_type type=%s", agent_type_str)
                continue

            agent_class = AGENT_MAP.get(agent_type)
            if not agent_class:
                continue

            agent = agent_class()

            # Create per-agent sub-logger
            agent_logger = run_log.for_agent(agent_type_str) if run_log else None

            task = asyncio.create_task(
                self._run_single_agent(
                    agent_name=agent_type_str,
                    agent=agent,
                    sources=sources,
                    run_config=run_config,
                    agent_logger=agent_logger,
                ),
                name=f"agent-{agent_type_str}",
            )
            tasks.append(task)

        if not tasks:
            return []

        results: list[tuple[str, dict, Optional[Exception]]] = []
        for coro in asyncio.as_completed(tasks):
            result = await coro
            results.append(result)

        return results

    async def _run_single_agent(
        self,
        agent_name: str,
        agent,
        sources: list[Source],
        run_config: Run,
        agent_logger=None,
    ) -> tuple[str, dict, Optional[Exception]]:
        """Execute one agent with timeout and error handling."""
        timeout = max(0, int(settings.agent_timeout_seconds))
        logger.info(
            "agent_start agent=%s sources=%d",
            agent_name,
            len(sources),
        )
        if agent_logger:
            agent_logger.info(
                "agent_start",
                step="pipeline",
                sources=len(sources),
            )

        try:
            if timeout > 0:
                result = await asyncio.wait_for(
                    agent.run(
                        sources=sources,
                        run_config=run_config,
                        run_logger=agent_logger,
                    ),
                    timeout=timeout,
                )
            else:
                result = await agent.run(
                    sources=sources,
                    run_config=run_config,
                    run_logger=agent_logger,
                )

            logger.info(
                "agent_complete agent=%s findings=%d errors=%d",
                agent_name,
                len(result["findings"]),
                len(result["errors"]),
            )
            if agent_logger:
                agent_logger.info(
                    "agent_complete",
                    step="pipeline",
                    findings=len(result["findings"]),
                    errors=len(result["errors"]),
                )
            return agent_name, result, None

        except asyncio.TimeoutError:
            logger.error("agent_timeout agent=%s timeout=%ds", agent_name, timeout)
            if agent_logger:
                agent_logger.error(
                    "agent_timeout",
                    step="pipeline",
                    timeout_seconds=timeout,
                )
            return (
                agent_name,
                {
                    **self._EMPTY_AGENT_RESULT,
                    "errors": [f"agent timeout after {timeout}s"],
                },
                RuntimeError(f"timed out after {timeout}s"),
            )
        except Exception as exc:
            logger.error("agent_error agent=%s err=%s", agent_name, str(exc)[:300])
            if agent_logger:
                agent_logger.error(
                    "agent_error",
                    step="pipeline",
                    error=str(exc)[:300],
                )
            return (
                agent_name,
                {**self._EMPTY_AGENT_RESULT, "errors": [str(exc)[:300]]},
                exc,
            )
        finally:
            try:
                await agent.close()
            except Exception:
                pass

    # ── Layer 3: Finding Persistence ───────────────────────────────

    async def _persist_findings(
        self,
        finding_dicts: list[dict],
        run_trigger_id: int,
        user_id: int,
        db: AsyncSession,
    ) -> None:
        """Persist all finding dicts as Finding records."""
        if not finding_dicts:
            return

        for fd in finding_dicts:
            finding = Finding(
                user_id=user_id,
                run_trigger_id=run_trigger_id,
                content=fd.get("content", ""),
                summary=fd.get("summary", ""),
                src_url=fd.get("src_url", ""),
                category=fd.get("category", "other"),
                confidence=fd.get("confidence", 0.5),
            )
            db.add(finding)

        await db.flush()
        logger.info("findings_persisted count=%d", len(finding_dicts))

    # ── Layer 4: Snapshot Generation ───────────────────────────────

    async def _create_snapshots(
        self,
        sources_by_type: dict[str, list[Source]],
        all_findings: list[dict],
        agent_statuses: dict[str, str],
        run_trigger_id: int,
        db: AsyncSession,
    ) -> list[int]:
        """Create per-source Snapshot records summarizing execution."""
        url_to_findings: dict[str, int] = {}
        for fd in all_findings:
            url = fd.get("src_url", "")
            url_to_findings[url] = url_to_findings.get(url, 0) + 1

        snapshot_ids: list[int] = []
        for agent_type_str, sources in sources_by_type.items():
            status = agent_statuses.get(agent_type_str, "completed")
            snap_status = "failed" if status == "failed" else "completed"

            for source in sources:
                findings_count = url_to_findings.get(source.url, 0)
                snapshot = Snapshot(
                    run_trigger_id=run_trigger_id,
                    source_id=source.id,
                    total_findings=findings_count,
                    summary=f"{agent_type_str}: {findings_count} findings from {source.display_name}",
                    status=snap_status,
                )
                db.add(snapshot)
                await db.flush()
                snapshot_ids.append(snapshot.id)

        logger.info("snapshots_created count=%d", len(snapshot_ids))
        return snapshot_ids

    # ── Layer 5-6: Digest + PDF/HTML ───────────────────────────────

    async def _generate_digest(
        self,
        trigger: RunTrigger,
        run: Run,
        findings: list[dict],
        snapshot_ids: list[int],
        user_id: int,
        db: AsyncSession,
    ) -> Digest | None:
        """Compile digest, generate PDF + HTML, persist Digest record."""
        try:
            digest_data = await self.digest_compiler.compile(
                run_trigger_id=trigger.id,
                findings=findings,
            )

            pdf_path: str | None = None
            html_path: str | None = None
            try:
                rendered_path = self.pdf_renderer.render(digest_data)
                if rendered_path.endswith(".html"):
                    html_path = rendered_path
                else:
                    pdf_path = rendered_path
                    # HTML is always generated alongside the PDF
                    html_path = rendered_path.replace(".pdf", ".html")
            except Exception as exc:
                logger.error("pdf_render_error err=%s", str(exc)[:200])

            digest = Digest(
                user_id=user_id,
                run_trigger_id=trigger.id,
                digest_name=digest_data.get("digest_title"),
                pdf_path=pdf_path,
                html_path=html_path,
                status="completed",
            )
            db.add(digest)
            await db.flush()

            for snap_id in snapshot_ids:
                link = DigestSnapshot(
                    digest_id=digest.id,
                    snapshot_id=snap_id,
                )
                db.add(link)

            await db.flush()
            logger.info(
                "digest_created digest_id=%s pdf=%s",
                digest.digest_id[:8],
                bool(pdf_path),
            )
            return digest

        except Exception as exc:
            logger.error("digest_generation_error err=%s", str(exc)[:300])
            return None

    # ── Layer 7: Email ─────────────────────────────────────────────

    async def _send_email(
        self,
        digest: Digest,
        recipients: list[str],
    ) -> None:
        """Send digest email if configured."""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            subject = f"Zentivra AI Radar - {today}"
            await self.email_service.send_digest_email(
                recipients=recipients,
                subject=subject,
                executive_summary="Your Zentivra AI Radar digest is ready.",
                pdf_path=digest.pdf_path,
            )
            logger.info("email_sent recipients=%d", len(recipients))
        except Exception as exc:
            logger.error("email_send_error err=%s", str(exc)[:200])
