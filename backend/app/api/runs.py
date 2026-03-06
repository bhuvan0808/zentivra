"""Runs API - Trigger runs and view run history."""

from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Query

from app.dependencies import get_run_service
from app.models.run import RunStatus
from app.models.source import AgentType
from app.schemas.run import (
    RunAgentActivityResponse,
    RunAgentLogResponse,
    RunAgentSummaryResponse,
    RunResponse,
    RunTriggerRequest,
    RunTriggerResponse,
)
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
    payload: RunTriggerRequest | None = None,
    service: RunService = Depends(get_run_service),
):
    """Manually trigger a new pipeline run."""
    run, options = await service.trigger(payload)
    background_tasks.add_task(_execute_run, run.id, options)
    return RunTriggerResponse(
        run_id=run.id,
        message="Run triggered successfully. Pipeline executing in background.",
        status=RunStatus.PENDING,
    )


@router.get("/{run_id}/agents", response_model=list[RunAgentSummaryResponse])
async def get_run_agents(
    run_id: str,
    service: RunService = Depends(get_run_service),
):
    """Get per-agent summary and progress for a run."""
    return await service.get_agent_summaries(run_id)


@router.get(
    "/{run_id}/agents/{agent_type}/activity",
    response_model=list[RunAgentActivityResponse],
)
async def get_run_agent_activity(
    run_id: str,
    agent_type: AgentType,
    limit: int = Query(200, ge=1, le=1000),
    service: RunService = Depends(get_run_service),
):
    """Get recent URL crawl activity for one agent in a run."""
    return await service.get_agent_activity(run_id, agent_type, limit=limit)


@router.get(
    "/{run_id}/agents/{agent_type}/logs",
    response_model=list[RunAgentLogResponse],
)
async def get_run_agent_logs(
    run_id: str,
    agent_type: AgentType,
    limit: int = Query(300, ge=1, le=1000),
    service: RunService = Depends(get_run_service),
):
    """Get recent execution logs for one agent in a run."""
    return await service.get_agent_logs(run_id, agent_type, limit=limit)


async def _execute_run(run_id: str, options: dict | None = None):
    """Execute the full pipeline via the Orchestrator."""
    from app.scheduler.orchestrator import Orchestrator

    orchestrator = Orchestrator()
    opts = options or {}
    await orchestrator.execute_run(
        run_id=run_id,
        agent_types=opts.get("agent_types"),
        source_ids=opts.get("source_ids"),
        recipients_override=opts.get("recipients"),
        max_sources_per_agent=opts.get("max_sources_per_agent"),
    )
