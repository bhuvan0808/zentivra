"""
Agents API
==========
URL prefix: /api/agents

Lists intelligence agents with live status and provides access to
per-agent execution logs and crawl sources. Status is derived from
active run triggers and the filesystem log directory.

Endpoints:
- GET  /api/agents                      → list all agents with status
- GET  /api/agents/{agent_key}/logs     → recent logs for a specific agent
- GET  /api/agents/{agent_key}/sources  → crawl sources for an agent
"""

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentUser, get_current_user
from app.models.run_trigger import RunTrigger
from app.models.run import Run
from app.models.source import Source

router = APIRouter(prefix="/agents", tags=["Agents"])

LOG_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "logs"

_STRIP_FIELDS = {"filename", "lineno", "line_number", "file_name", "pathname"}

AGENT_DEFINITIONS = {
    "competitor": {
        "label": "Competitor Watcher",
        "description": "Monitors competitor announcements, releases, and strategic moves.",
    },
    "model_provider": {
        "label": "Model Provider Watcher",
        "description": "Tracks LLM provider updates, new model releases, and API changes.",
    },
    "research": {
        "label": "Research Scout",
        "description": "Scans research publications, arXiv papers, and technical blogs.",
    },
    "hf_benchmark": {
        "label": "HF Benchmark Tracker",
        "description": "Monitors Hugging Face leaderboards and benchmark results.",
    },
}


@router.get("")
async def list_agents(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """
    GET /api/agents
    Auth: Bearer token required.
    Response: list of agent objects with status, source count, and latest log info.
    """
    # Identify agents that are currently running via active triggers
    running_agents: set[str] = set()
    stmt = (
        select(RunTrigger.run_trigger_id)
        .join(Run, RunTrigger.run_id == Run.id)
        .where(Run.user_id == user.id)
        .where(RunTrigger.status.in_(["running", "pending"]))
    )
    result = await db.execute(stmt)
    running_trigger_ids = [row[0] for row in result.all()]

    for trigger_id in running_trigger_ids:
        trigger_log_dir = LOG_DIR / trigger_id
        if trigger_log_dir.is_dir():
            for child in trigger_log_dir.iterdir():
                if child.is_dir():
                    running_agents.add(child.name)

    # Count enabled sources per agent type for this user
    stmt = (
        select(Source.agent_type, func.count())
        .where(Source.user_id == user.id)
        .where(Source.is_enabled == True)  # noqa: E712
        .group_by(Source.agent_type)
    )
    result = await db.execute(stmt)
    source_counts = dict(result.all())

    # Find the latest trigger with logs for each agent
    latest_logs: dict[str, dict] = {}
    stmt = (
        select(RunTrigger.run_trigger_id, RunTrigger.status, RunTrigger.created_at)
        .join(Run, RunTrigger.run_id == Run.id)
        .where(Run.user_id == user.id)
        .order_by(RunTrigger.created_at.desc())
        .limit(20)
    )
    result = await db.execute(stmt)
    recent_triggers = result.all()

    for trigger_id, status, created_at in recent_triggers:
        trigger_log_dir = LOG_DIR / trigger_id
        if not trigger_log_dir.is_dir():
            continue
        for child in sorted(trigger_log_dir.iterdir()):
            if not child.is_dir():
                continue
            agent_name = child.name
            if agent_name not in latest_logs:
                log_file = child / "logs.ndjson"
                if log_file.exists():
                    latest_logs[agent_name] = {
                        "trigger_id": trigger_id,
                        "trigger_status": status,
                        "created_at": (
                            created_at.isoformat() if created_at else None
                        ),
                    }

    agents = []
    for key, defn in AGENT_DEFINITIONS.items():
        agents.append(
            {
                "key": key,
                "label": defn["label"],
                "description": defn["description"],
                "status": "running" if key in running_agents else "idle",
                "sources_count": source_counts.get(key, 0),
                "latest_log": latest_logs.get(key),
            }
        )

    return agents


@router.get("/{agent_key}/logs")
async def get_agent_logs(
    agent_key: str,
    trigger_id: str | None = Query(
        None, description="Specific trigger ID to fetch logs from"
    ),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """
    GET /api/agents/{agent_key}/logs
    Auth: Bearer token required.
    Response: { agent_key, trigger_id, total_lines, entries[] }.

    If trigger_id is provided, returns logs from that trigger.
    Otherwise, returns logs from the most recent trigger with data for this agent.
    """
    if agent_key not in AGENT_DEFINITIONS:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {agent_key}")

    if trigger_id:
        # Verify ownership
        stmt = (
            select(RunTrigger)
            .join(Run, RunTrigger.run_id == Run.id)
            .where(Run.user_id == user.id)
            .where(RunTrigger.run_trigger_id == trigger_id)
        )
        result = await db.execute(stmt)
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Trigger not found")
    else:
        # Find the latest trigger with logs for this agent
        stmt = (
            select(RunTrigger.run_trigger_id)
            .join(Run, RunTrigger.run_id == Run.id)
            .where(Run.user_id == user.id)
            .order_by(RunTrigger.created_at.desc())
            .limit(20)
        )
        result = await db.execute(stmt)
        recent = result.all()

        trigger_id = None
        for (tid,) in recent:
            log_file = LOG_DIR / tid / agent_key / "logs.ndjson"
            if log_file.exists():
                trigger_id = tid
                break

        if not trigger_id:
            return {
                "agent_key": agent_key,
                "trigger_id": None,
                "total_lines": 0,
                "entries": [],
            }

    log_file = LOG_DIR / trigger_id / agent_key / "logs.ndjson"
    if not log_file.exists():
        return {
            "agent_key": agent_key,
            "trigger_id": trigger_id,
            "total_lines": 0,
            "entries": [],
        }

    entries: list[dict] = []
    total_lines = 0

    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            total_lines += 1
            if len(entries) < limit:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    for field in _STRIP_FIELDS:
                        entry.pop(field, None)
                    entries.append(entry)
                except json.JSONDecodeError:
                    continue

    return {
        "agent_key": agent_key,
        "trigger_id": trigger_id,
        "total_lines": total_lines,
        "entries": entries,
    }


@router.get("/{agent_key}/sources")
async def get_agent_sources(
    agent_key: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """
    GET /api/agents/{agent_key}/sources
    Auth: Bearer token required.
    Response: list of { source_id, source_name, display_name, url, is_enabled }.
    """
    if agent_key not in AGENT_DEFINITIONS:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {agent_key}")

    stmt = (
        select(
            Source.source_id,
            Source.source_name,
            Source.display_name,
            Source.url,
            Source.is_enabled,
        )
        .where(Source.user_id == user.id)
        .where(Source.agent_type == agent_key)
        .order_by(Source.display_name)
    )
    result = await db.execute(stmt)
    sources = [
        {
            "source_id": row.source_id,
            "source_name": row.source_name,
            "display_name": row.display_name,
            "url": row.url,
            "is_enabled": row.is_enabled,
        }
        for row in result.all()
    ]
    return sources
