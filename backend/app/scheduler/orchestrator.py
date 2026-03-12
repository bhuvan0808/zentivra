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

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session
from app.digest.compiler import DigestCompiler
from app.digest.pdf_renderer import PDFRenderer
from app.models.digest import Digest
from app.models.digest_snapshot import DigestSnapshot
from app.models.agent_log import AgentLog
from app.models.finding import Finding
from app.models.run import Run
from app.models.run_trigger import RunTrigger
from app.models.snapshot import Snapshot
from app.models.source import AgentType, Source
from app.notifications.email_service import EmailService
from app.scheduler.agent_graph import run_agents_with_langgraph
from app.utils.logger import logger
from app.utils.run_logger import RunLogger

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

                    # Tag each finding with its agent_type so the digest
                    # compiler can group them into the correct sections.
                    for fd in findings:
                        fd.setdefault("agent_type", agent_name)
                        fd.setdefault("source_url", fd.get("src_url", ""))
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

                # ── 3b. Fallback to previous findings if none produced ─
                # Ensures PDF is never empty on re-trigger; reuses latest
                # completed trigger's findings for the same run.
                used_cached_findings = False
                if not all_finding_dicts:
                    cached = await self._get_previous_findings(
                        run.id, trigger.id, db
                    )
                    if cached:
                        all_finding_dicts = cached
                        used_cached_findings = True
                        logger.info(
                            "findings_cache_hit count=%d run_id=%s",
                            len(cached),
                            run.run_id[:8],
                        )
                        run_log.info(
                            "findings_cache_hit",
                            step="finding_persist",
                            cached_count=len(cached),
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
                        cached=used_cached_findings,
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
                elif used_cached_findings:
                    # Have findings but they came from cache
                    trigger.status = "completed"
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
                # Generate when pdf enabled and findings exist (including cached).
                digest_record = None
                if (
                    run.enable_pdf_gen
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
                # Persist logs to DB so they survive Render deploys
                try:
                    await self._persist_logs_to_db(
                        trigger.run_trigger_id, run_user_id, db
                    )
                    await db.commit()
                except Exception as exc:
                    logger.error(
                        "log_db_persistence_failed err=%s", str(exc)[:200]
                    )

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

    # ── Layer 2: Parallel Agent Execution (LangGraph) ────────────

    async def _run_agents_parallel(
        self,
        sources_by_type: dict[str, list[Source]],
        run_config: Run,
        run_log: RunLogger | None = None,
    ) -> list[tuple[str, dict, Optional[Exception]]]:
        """Run all agent types in parallel using LangGraph.

        Each agent type gets its own graph node and runs concurrently.
        Returns structured results: list of (agent_name, result_dict, error).
        """
        return await run_agents_with_langgraph(
            sources_by_type=sources_by_type,
            run_config=run_config,
            run_log=run_log,
        )

    # ── Layer 2b: Previous Findings Cache ─────────────────────────

    async def _get_previous_findings(
        self,
        run_id: int,
        current_trigger_id: int,
        db: AsyncSession,
    ) -> list[dict]:
        """Fetch findings from the most recent completed trigger of the same run.

        Used as a fallback when the current trigger produces 0 findings,
        ensuring the PDF digest is never empty on re-triggers.

        Returns list of finding dicts (same format as agent output), or [].
        """
        # Find the latest completed trigger for this run (not the current one)
        prev_trigger = await db.execute(
            select(RunTrigger)
            .where(
                and_(
                    RunTrigger.run_id == run_id,
                    RunTrigger.id != current_trigger_id,
                    RunTrigger.status.in_(["completed", "partial"]),
                )
            )
            .order_by(desc(RunTrigger.created_at))
            .limit(1)
        )
        prev = prev_trigger.scalar_one_or_none()
        if not prev:
            return []

        # Fetch findings from that trigger
        findings_result = await db.execute(
            select(Finding).where(Finding.run_trigger_id == prev.id)
        )
        findings = list(findings_result.scalars().all())
        if not findings:
            return []

        # Convert to dicts matching agent output format, restoring rich fields from meta
        result = []
        for f in findings:
            fd = {
                "content": f.content or "",
                "summary": f.summary or "",
                "src_url": f.src_url or "",
                "source_url": f.src_url or "",
                "category": f.category or "other",
                "confidence": f.confidence or 0.5,
            }
            if f.meta and isinstance(f.meta, dict):
                fd.update(f.meta)
            result.append(fd)
        return result

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

        # Keys stored in the meta JSONB column for PDF rendering on cache fallback
        _META_KEYS = (
            "title", "summary_short", "summary_long", "why_it_matters",
            "what_changed", "who_it_affects", "key_numbers", "tags",
            "entities", "evidence", "publisher", "agent_type",
            "relevance_score", "novelty_score", "credibility_score",
            "actionability_score", "impact_score",
        )

        for fd in finding_dicts:
            meta = {k: fd[k] for k in _META_KEYS if k in fd and fd[k]}
            finding = Finding(
                user_id=user_id,
                run_trigger_id=run_trigger_id,
                content=fd.get("content", ""),
                summary=fd.get("summary", ""),
                src_url=fd.get("src_url", ""),
                category=fd.get("category", "other"),
                confidence=fd.get("confidence", 0.5),
                meta=meta or None,
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

    # ── Layer 8: Log Persistence ──────────────────────────────────

    async def _persist_logs_to_db(
        self,
        trigger_id: str,
        user_id: int,
        db: AsyncSession,
    ) -> None:
        """
        Read NDJSON log files from disk and persist to agent_logs table.

        Called after run_log.close() to ensure files are fully written.
        Existing records for the same (trigger_id, agent_key) are updated.
        """
        trigger_log_dir = LOG_DIR / trigger_id
        if not trigger_log_dir.is_dir():
            return

        for child in trigger_log_dir.iterdir():
            if not child.is_dir():
                continue

            agent_key = child.name
            log_file = child / "logs.ndjson"
            if not log_file.exists():
                continue

            entries: list[dict] = []
            total_lines = 0
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    total_lines += 1
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

            # Upsert: update if exists, create if new
            existing = await db.execute(
                select(AgentLog)
                .where(AgentLog.trigger_id == trigger_id)
                .where(AgentLog.agent_key == agent_key)
            )
            record = existing.scalar_one_or_none()
            if record:
                record.entries = entries
                record.total_lines = total_lines
            else:
                db.add(
                    AgentLog(
                        user_id=user_id,
                        trigger_id=trigger_id,
                        agent_key=agent_key,
                        entries=entries,
                        total_lines=total_lines,
                    )
                )

        await db.flush()
        logger.info("logs_persisted_to_db trigger=%s", trigger_id[:8])
