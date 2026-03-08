"""
Dashboard API
=============
URL prefix: /api/dashboard

Endpoints are split into independent tiles for progressive loading. The frontend
can fetch each tile separately (KPI, charts, triggers, sources) so the UI
renders incrementally without waiting for a single large response.
All endpoints require authentication.
"""

from datetime import date, datetime, timedelta, timezone

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

_ALL_STATUSES = [
    "completed",
    "failed",
    "partial",
    "completed_empty",
    "running",
    "pending",
]


@router.get("/kpi")
async def get_kpi(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """
    GET /api/dashboard/kpi
    Auth: Bearer token required.
    Response: {total_findings, total_sources, runs_overview}.
    Tile: KPI summary (findings count, sources count, runs overview).
    """
    uid = user.id

    total_findings = (
        await db.execute(select(func.count(Finding.id)).where(Finding.user_id == uid))
    ).scalar() or 0

    total_sources = (
        await db.execute(
            select(func.count(Source.id)).where(
                Source.is_enabled == True, Source.user_id == uid  # noqa: E712
            )
        )
    ).scalar() or 0

    total_runs = (
        await db.execute(select(func.count(Run.id)).where(Run.user_id == uid))
    ).scalar() or 0

    enabled_runs = (
        await db.execute(
            select(func.count(Run.id)).where(
                Run.user_id == uid, Run.is_enabled == True  # noqa: E712
            )
        )
    ).scalar() or 0

    return {
        "total_findings": total_findings,
        "total_sources": total_sources,
        "runs_overview": {
            "total_runs": total_runs,
            "enabled_runs": enabled_runs,
        },
    }


@router.get("/charts")
async def get_charts(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """
    GET /api/dashboard/charts
    Auth: Bearer token required.
    Response: {confidence_distribution, daily_findings, confidence_trend,
    by_category, by_agent_type}.
    Tiles: Charts (confidence distribution, daily findings, confidence trend,
    findings by category, agent performance).
    """
    uid = user.id

    # ── Confidence distribution ──────────────────────────────────────────
    conf_result = await db.execute(
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
    row = conf_result.fetchone()
    confidence_distribution = {
        "high": int(row[0] or 0) if row else 0,
        "medium": int(row[1] or 0) if row else 0,
        "low": int(row[2] or 0) if row else 0,
    }

    # ── Daily findings (last 30 days) ────────────────────────────────────
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    date_col = func.date(Finding.created_at)

    daily_result = await db.execute(
        select(date_col.label("d"), func.count(Finding.id))
        .where(Finding.user_id == uid, Finding.created_at >= cutoff)
        .group_by(date_col)
        .order_by(date_col)
    )
    daily_map: dict[date, int] = {}
    for d, count in daily_result.all():
        day = d if isinstance(d, date) else date.fromisoformat(str(d))
        daily_map[day] = count

    today = date.today()
    daily_findings = [
        {
            "date": (today - timedelta(days=i)).isoformat(),
            "count": daily_map.get(today - timedelta(days=i), 0),
        }
        for i in range(30, -1, -1)
    ]

    # ── Average confidence trend (last 30 days) ──────────────────────────
    conf_trend_result = await db.execute(
        select(date_col.label("d"), func.avg(Finding.confidence))
        .where(Finding.user_id == uid, Finding.created_at >= cutoff)
        .group_by(date_col)
        .order_by(date_col)
    )
    conf_map: dict[date, float | None] = {}
    for d, avg_conf in conf_trend_result.all():
        day = d if isinstance(d, date) else date.fromisoformat(str(d))
        conf_map[day] = round(float(avg_conf), 2) if avg_conf is not None else None

    confidence_trend = [
        {
            "date": (today - timedelta(days=i)).isoformat(),
            "avg_confidence": conf_map.get(today - timedelta(days=i)),
        }
        for i in range(30, -1, -1)
    ]

    # ── Findings by category ─────────────────────────────────────────────
    cat_result = await db.execute(
        select(Finding.category, func.count(Finding.id))
        .where(Finding.user_id == uid)
        .group_by(Finding.category)
    )
    by_category = {row[0]: row[1] for row in cat_result.all() if row[0]}

    # ── Agent performance (by agent_type) ────────────────────────────────
    agent_result = await db.execute(
        select(Source.agent_type, func.count(Finding.id))
        .select_from(Finding)
        .join(RunTrigger, Finding.run_trigger_id == RunTrigger.id)
        .join(Snapshot, Snapshot.run_trigger_id == RunTrigger.id)
        .join(Source, Snapshot.source_id == Source.id)
        .where(Finding.user_id == uid)
        .group_by(Source.agent_type)
    )
    by_agent_type = {row[0]: row[1] for row in agent_result.all() if row[0]}

    return {
        "confidence_distribution": confidence_distribution,
        "daily_findings": daily_findings,
        "confidence_trend": confidence_trend,
        "by_category": by_category,
        "by_agent_type": by_agent_type,
    }


@router.get("/triggers")
async def get_triggers(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """
    GET /api/dashboard/triggers
    Auth: Bearer token required.
    Response: {trigger_status_counts, recent_triggers}.
    Tiles: Trigger status counts and recent activity list.
    """
    uid = user.id

    # ── Trigger status counts ────────────────────────────────────────────
    counts_result = await db.execute(
        select(RunTrigger.status, func.count(RunTrigger.id))
        .join(Run, RunTrigger.run_id == Run.id)
        .where(Run.user_id == uid)
        .group_by(RunTrigger.status)
    )
    trigger_status_counts = {s: 0 for s in _ALL_STATUSES}
    for status, count in counts_result.all():
        if status in trigger_status_counts:
            trigger_status_counts[status] = count

    # ── Recent triggers (last 10) ────────────────────────────────────────
    rt_result = await db.execute(
        select(RunTrigger)
        .join(Run, RunTrigger.run_id == Run.id)
        .where(Run.user_id == uid)
        .options(joinedload(RunTrigger.run))
        .order_by(RunTrigger.created_at.desc())
        .limit(10)
    )
    recent_objs = rt_result.scalars().all()

    recent_triggers = [
        {
            "run_trigger_id": rt.run_trigger_id,
            "run_name": rt.run.run_name if rt.run else "Unknown",
            "status": rt.status,
            "findings_count": len(rt.findings) if rt.findings else 0,
            "snapshots_count": len(rt.snapshots) if rt.snapshots else 0,
            "created_at": rt.created_at.isoformat() if rt.created_at else None,
        }
        for rt in recent_objs
    ]

    return {
        "trigger_status_counts": trigger_status_counts,
        "recent_triggers": recent_triggers,
    }


@router.get("/sources")
async def get_sources(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """
    GET /api/dashboard/sources
    Auth: Bearer token required.
    Response: {findings_by_source}.
    Tile: Top sources ranked by total findings produced.
    """
    uid = user.id

    result = await db.execute(
        select(
            Source.source_name,
            Source.display_name,
            func.coalesce(func.sum(Snapshot.total_findings), 0).label("cnt"),
        )
        .select_from(Snapshot)
        .join(Source, Snapshot.source_id == Source.id)
        .join(RunTrigger, Snapshot.run_trigger_id == RunTrigger.id)
        .join(Run, RunTrigger.run_id == Run.id)
        .where(Run.user_id == uid)
        .group_by(Source.id, Source.source_name, Source.display_name)
        .order_by(func.sum(Snapshot.total_findings).desc())
        .limit(8)
    )

    return {
        "findings_by_source": [
            {"source_name": row[0], "display_name": row[1], "count": int(row[2])}
            for row in result.all()
        ],
    }
