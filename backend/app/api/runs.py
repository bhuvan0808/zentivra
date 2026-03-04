"""Runs API - Trigger runs and view run history."""

import asyncio
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.run import Run, RunStatus
from app.schemas.run import RunResponse, RunTriggerResponse

router = APIRouter(prefix="/runs", tags=["Runs"])


@router.get("/", response_model=list[RunResponse])
async def list_runs(
    status: Optional[RunStatus] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List runs, optionally filtered by status."""
    query = select(Run).order_by(Run.started_at.desc()).limit(limit)
    if status:
        query = query.where(Run.status == status)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(run_id: str, db: AsyncSession = Depends(get_db)):
    """Get detailed run info including per-agent statuses."""
    result = await db.execute(select(Run).where(Run.id == run_id))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.post("/trigger", response_model=RunTriggerResponse, status_code=202)
async def trigger_run(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger a new pipeline run."""
    # Check if a run is already in progress
    result = await db.execute(
        select(Run).where(Run.status == RunStatus.RUNNING)
    )
    existing_run = result.scalar_one_or_none()
    if existing_run:
        raise HTTPException(
            status_code=409,
            detail=f"Run {existing_run.id} is already in progress.",
        )

    # Create a new run
    run = Run(triggered_by="manual")
    db.add(run)
    await db.flush()
    await db.refresh(run)

    # Schedule the pipeline in the background
    # (Orchestrator will be connected in Phase 5)
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

