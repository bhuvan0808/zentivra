"""Runs API - Trigger runs and view run history."""

from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Query

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


async def _execute_run(run_id: str):
    """Execute the full pipeline via the Orchestrator."""
    from app.scheduler.orchestrator import Orchestrator

    orchestrator = Orchestrator()
    await orchestrator.execute_run(run_id)
