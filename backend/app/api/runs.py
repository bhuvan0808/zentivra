"""Runs API - CRUD for run configurations and trigger endpoint."""

import traceback

from fastapi import APIRouter, BackgroundTasks, Depends, Query

from app.dependencies import CurrentUser, get_current_user, get_run_service
from app.schemas.run import (
    RunCreate,
    RunCreateResponse,
    RunResponse,
    RunTriggerDetailResponse,
    RunTriggerRequest,
    RunTriggerResponse,
    RunUpdate,
)
from app.scheduler.scheduler import sync_scheduler
from app.services.run_service import RunService

router = APIRouter(prefix="/runs", tags=["Runs"])


# ── CRUD (all protected) ───────────────────────────────────


@router.get("/", response_model=list[RunResponse])
async def list_runs(
    limit: int = Query(20, ge=1, le=100),
    service: RunService = Depends(get_run_service),
    user: CurrentUser = Depends(get_current_user),
):
    """List run configurations, most recent first."""
    return await service.list_runs(user.id, limit=limit)


@router.post("/", response_model=RunCreateResponse, status_code=201)
async def create_run(
    run_data: RunCreate,
    background_tasks: BackgroundTasks,
    service: RunService = Depends(get_run_service),
    user: CurrentUser = Depends(get_current_user),
):
    """Create a new run configuration. Optionally trigger immediately."""
    run = await service.create(run_data, user.id)
    await sync_scheduler()

    trigger_resp = None
    if run_data.trigger_on_create:
        trigger, _, options = await service.trigger(run.run_id, user.id)
        background_tasks.add_task(_execute_run, trigger.id, run.id, options)
        trigger_resp = RunTriggerResponse(
            run_trigger_id=trigger.run_trigger_id,
            run_id=run.run_id,
            message="Run triggered successfully. Pipeline executing in background.",
            status=trigger.status,
        )

    return RunCreateResponse(
        run_id=run.run_id,
        run_name=run.run_name,
        description=run.description,
        enable_pdf_gen=run.enable_pdf_gen,
        enable_email_alert=run.enable_email_alert,
        sources=run.sources,
        crawl_frequency=run.crawl_frequency,
        crawl_depth=run.crawl_depth,
        keywords=run.keywords,
        is_enabled=run.is_enabled,
        created_at=run.created_at,
        updated_at=run.updated_at,
        trigger=trigger_resp,
    )


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(
    run_id: str,
    service: RunService = Depends(get_run_service),
    user: CurrentUser = Depends(get_current_user),
):
    """Get a run configuration by its UUID."""
    return await service.get_by_uuid(run_id, user.id)


@router.put("/{run_id}", response_model=RunResponse)
async def update_run(
    run_id: str,
    run_data: RunUpdate,
    service: RunService = Depends(get_run_service),
    user: CurrentUser = Depends(get_current_user),
):
    """Update a run configuration by its UUID."""
    result = await service.update(run_id, run_data, user.id)
    await sync_scheduler()
    return result


@router.delete("/{run_id}", status_code=204)
async def delete_run(
    run_id: str,
    service: RunService = Depends(get_run_service),
    user: CurrentUser = Depends(get_current_user),
):
    """Delete a run configuration by its UUID."""
    await service.delete(run_id, user.id)
    await sync_scheduler()


# ── Trigger ─────────────────────────────────────────────────


@router.post("/{run_id}/trigger", response_model=RunTriggerResponse, status_code=202)
async def trigger_run(
    run_id: str,
    background_tasks: BackgroundTasks,
    payload: RunTriggerRequest | None = None,
    service: RunService = Depends(get_run_service),
    user: CurrentUser = Depends(get_current_user),
):
    """Trigger execution of a run configuration."""
    trigger, run, options = await service.trigger(run_id, user.id, payload)

    background_tasks.add_task(
        _execute_run, trigger.id, run.id, options
    )

    return RunTriggerResponse(
        run_trigger_id=trigger.run_trigger_id,
        run_id=run.run_id,
        message="Run triggered successfully. Pipeline executing in background.",
        status=trigger.status,
    )


async def _execute_run(
    run_trigger_id: int, run_id: int, options: dict | None = None
):
    """Background task: execute the full pipeline via the Orchestrator."""
    from app.utils.logger import logger

    try:
        from app.scheduler.orchestrator import Orchestrator

        orchestrator = Orchestrator()
        await orchestrator.execute(
            run_trigger_id=run_trigger_id,
            run_id=run_id,
            options=options or {},
        )
    except Exception:
        logger.error(
            "background_task_failed run_trigger_id=%s\n%s",
            run_trigger_id,
            traceback.format_exc(),
        )


# ── Trigger history ─────────────────────────────────────────


@router.get("/{run_id}/triggers", response_model=list[RunTriggerDetailResponse])
async def list_triggers_for_run(
    run_id: str,
    limit: int = Query(50, ge=1, le=200),
    service: RunService = Depends(get_run_service),
    user: CurrentUser = Depends(get_current_user),
):
    """List trigger history for a run (newest first)."""
    triggers = await service.get_triggers_for_run(run_id, user.id, limit=limit)
    results = []
    for t in triggers:
        digest_id = None
        digest_status = None
        pdf_url = None
        html_url = None
        if t.digests:
            d = t.digests[0]
            digest_id = d.digest_id
            digest_status = d.status
            pdf_url = d.pdf_path
            html_url = d.html_path

        results.append(
            RunTriggerDetailResponse(
                run_trigger_id=t.run_trigger_id,
                run_id=t.run.run_id if t.run else None,
                trigger_method=t.trigger_method,
                status=t.status,
                is_latest=t.is_latest,
                created_at=t.created_at,
                updated_at=t.updated_at,
                findings_count=len(t.findings) if t.findings else 0,
                snapshots_count=len(t.snapshots) if t.snapshots else 0,
                digest_id=digest_id,
                digest_status=digest_status,
                pdf_url=pdf_url,
                html_url=html_url,
            )
        )
    return results
