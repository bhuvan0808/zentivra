"""Dashboard API - Aggregated statistics for the command centre."""

from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.dependencies import CurrentUser, get_current_user
from app.models.finding import Finding
from app.models.run import Run
from app.models.run_trigger import RunTrigger
from app.models.snapshot import Snapshot
from app.models.source import Source

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Fetch aggregated statistics for the dashboard in a single query."""
    uid = user.id

    cat_result = await db.execute(
        select(Finding.category, func.count(Finding.id))
        .where(Finding.user_id == uid)
        .group_by(Finding.category)
    )
    by_category = {row[0]: row[1] for row in cat_result.all() if row[0]}

    total_findings_result = await db.execute(
        select(func.count(Finding.id)).where(Finding.user_id == uid)
    )
    total_findings = total_findings_result.scalar() or 0

    total_sources_result = await db.execute(
        select(func.count(Source.id)).where(
            Source.is_enabled == True, Source.user_id == uid  # noqa: E712
        )
    )
    total_sources = total_sources_result.scalar() or 0

    agent_types_result = await db.execute(
        select(Source.agent_type, func.count(Finding.id))
        .select_from(Finding)
        .join(RunTrigger, Finding.run_trigger_id == RunTrigger.id)
        .join(Snapshot, Snapshot.run_trigger_id == RunTrigger.id)
        .join(Source, Snapshot.source_id == Source.id)
        .where(Finding.user_id == uid)
        .group_by(Source.agent_type)
    )
    by_agent_type = {row[0]: row[1] for row in agent_types_result.all() if row[0]}

    confidence_result = await db.execute(
        select(
            func.sum(case((Finding.confidence >= 0.7, 1), else_=0)).label("high"),
            func.sum(
                case(
                    ((Finding.confidence >= 0.3) & (Finding.confidence < 0.7), 1),
                    else_=0,
                )
            ).label("medium"),
            func.sum(case((Finding.confidence < 0.3, 1), else_=0)).label("low"),
        ).where(Finding.user_id == uid)
    )
    conf_row = confidence_result.fetchone()
    confidence_distribution = {
        "high": int(conf_row[0] or 0) if conf_row else 0,
        "medium": int(conf_row[1] or 0) if conf_row else 0,
        "low": int(conf_row[2] or 0) if conf_row else 0,
    }

    recent_triggers_query = (
        select(RunTrigger)
        .join(Run, RunTrigger.run_id == Run.id)
        .where(Run.user_id == uid)
        .options(joinedload(RunTrigger.run))
        .order_by(RunTrigger.created_at.desc())
        .limit(10)
    )
    recent_triggers_result = await db.execute(recent_triggers_query)
    recent_triggers_objs = recent_triggers_result.scalars().all()

    recent_triggers = []
    for rt in recent_triggers_objs:
        recent_triggers.append(
            {
                "run_trigger_id": rt.run_trigger_id,
                "run_name": rt.run.run_name if rt.run else "Unknown",
                "status": rt.status,
                "findings_count": len(rt.findings) if rt.findings else 0,
                "snapshots_count": len(rt.snapshots) if rt.snapshots else 0,
                "created_at": rt.created_at.isoformat() if rt.created_at else None,
            }
        )

    timeline = []
    for rt in reversed(recent_triggers_objs):
        timeline.append(
            {
                "trigger_id": rt.run_trigger_id,
                "date": rt.created_at.strftime("%H:%M") if rt.created_at else "Unknown",
                "full_date": (
                    rt.created_at.strftime("%b %d, %H:%M")
                    if rt.created_at
                    else "Unknown"
                ),
                "count": len(rt.findings) if rt.findings else 0,
            }
        )

    return {
        "total_findings": total_findings,
        "total_sources": total_sources,
        "by_category": by_category,
        "by_agent_type": by_agent_type,
        "confidence_distribution": confidence_distribution,
        "recent_triggers": recent_triggers,
        "findings_timeline": timeline,
    }
