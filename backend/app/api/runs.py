"""Runs API - Trigger runs, view run history, and stream execution logs."""

import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

from app.dependencies import get_run_service
from app.models.run import RunStatus
from app.schemas.run import RunResponse, RunTriggerResponse
from app.services.run_service import RunService

router = APIRouter(prefix="/runs", tags=["Runs"])


@router.get("/", response_model=list[RunResponse])
async def list_runs(
    status: Optional[RunStatus] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    service: RunService = Depends(get_run_service),
):
    """List runs, optionally filtered by status."""
    return await service.list_runs(status=status, limit=limit)


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(
    run_id: str,
    service: RunService = Depends(get_run_service),
):
    """Get detailed run info including per-agent statuses."""
    return await service.get_by_id(run_id)


@router.post("/trigger", response_model=RunTriggerResponse, status_code=202)
async def trigger_run(
    background_tasks: BackgroundTasks,
    service: RunService = Depends(get_run_service),
):
    """Manually trigger a new pipeline run."""
    run = await service.trigger()
    background_tasks.add_task(_execute_run, run.id)
    return RunTriggerResponse(
        run_id=run.id,
        message="Run triggered successfully. Pipeline executing in background.",
        status=RunStatus.PENDING,
    )


@router.get("/{run_id}/logs")
async def get_run_logs(
    run_id: str,
    agent: Optional[str] = Query(None, description="Filter by agent type"),
    level: Optional[str] = Query(None, description="Filter by log level (INFO, WARNING, ERROR)"),
    phase: Optional[str] = Query(None, description="Filter by phase (fetch, extract, summarize, ...)"),
    tail: int = Query(200, ge=1, le=2000, description="Return last N log entries"),
    service: RunService = Depends(get_run_service),
):
    """
    Retrieve NDJSON execution logs for a pipeline run.

    Each entry is a JSON object with ts, level, agent, phase, event, and extra data.
    Supports filtering by agent, level, and phase. Returns the last `tail` entries.
    """
    run = await service.get_by_id(run_id)

    if not run.log_path:
        raise HTTPException(status_code=404, detail="No logs available for this run")

    log_file = Path(run.log_path)
    if not log_file.exists():
        raise HTTPException(status_code=404, detail="Log file not found on disk")

    entries = []
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            if agent and entry.get("agent") != agent:
                continue
            if level and entry.get("level", "").upper() != level.upper():
                continue
            if phase and entry.get("phase") != phase:
                continue

            entries.append(entry)

    return entries[-tail:]


async def _execute_run(run_id: str):
    """Execute the full pipeline via the Orchestrator."""
    import traceback
    from app.utils.logger import logger

    try:
        from app.scheduler.orchestrator import Orchestrator

        orchestrator = Orchestrator()
        await orchestrator.execute_run(run_id)
    except Exception:
        logger.error("background_task_failed run_id=%s\n%s", run_id, traceback.format_exc())
