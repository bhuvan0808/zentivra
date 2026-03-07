"""Run Triggers API - Query individual trigger executions and their results."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.run_trigger import RunTrigger
from app.models.user import User
from app.repositories.run_trigger_repository import RunTriggerRepository
from app.schemas.finding import FindingResponse
from app.schemas.run import RunTriggerDetailResponse
from app.schemas.snapshot import SnapshotResponse

router = APIRouter(
    prefix="/run-triggers",
    tags=["Run Triggers"],
    dependencies=[Depends(get_current_user)],
)


async def _get_trigger(trigger_id: str, db: AsyncSession) -> RunTrigger:
    repo = RunTriggerRepository(db)
    trigger = await repo.get_by_uuid(trigger_id)
    if not trigger:
        raise HTTPException(status_code=404, detail="Run trigger not found")
    return trigger


@router.get("/{run_trigger_id}", response_model=RunTriggerDetailResponse)
async def get_trigger(
    run_trigger_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a single trigger execution by UUID."""
    trigger = await _get_trigger(run_trigger_id, db)
    digest = trigger.digests[0] if trigger.digests else None
    return RunTriggerDetailResponse(
        run_trigger_id=trigger.run_trigger_id,
        run_id=trigger.run.run_id if trigger.run else None,
        trigger_method=trigger.trigger_method,
        status=trigger.status,
        is_latest=trigger.is_latest,
        created_at=trigger.created_at,
        updated_at=trigger.updated_at,
        findings_count=len(trigger.findings) if trigger.findings else 0,
        snapshots_count=len(trigger.snapshots) if trigger.snapshots else 0,
        digest_id=digest.digest_id if digest else None,
        digest_status=digest.status if digest else None,
    )


@router.get("/{run_trigger_id}/findings", response_model=list[FindingResponse])
async def list_trigger_findings(
    run_trigger_id: str,
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """List findings produced by a specific trigger execution."""
    trigger = await _get_trigger(run_trigger_id, db)
    findings = (trigger.findings or [])[:limit]
    return [
        FindingResponse(
            finding_id=f.finding_id,
            content=f.content,
            summary=f.summary,
            run_trigger_id=trigger.run_trigger_id,
            src_url=f.src_url,
            category=f.category,
            confidence=f.confidence,
            created_at=f.created_at,
        )
        for f in findings
    ]


@router.get("/{run_trigger_id}/snapshots", response_model=list[SnapshotResponse])
async def list_trigger_snapshots(
    run_trigger_id: str,
    db: AsyncSession = Depends(get_db),
):
    """List snapshots (per-source summaries) for a trigger execution."""
    trigger = await _get_trigger(run_trigger_id, db)
    snapshots = trigger.snapshots or []
    return [
        SnapshotResponse(
            snapshot_id=s.snapshot_id,
            source_name=s.source.display_name if s.source else None,
            total_findings=s.total_findings,
            summary=s.summary,
            status=s.status,
            created_at=s.created_at,
        )
        for s in snapshots
    ]
