"""
Agents API
==========
URL prefix: /api/agents

Lists intelligence agents with live status and provides access to
per-agent execution logs and crawl sources. Logs are read from the DB
(agent_logs table) with filesystem fallback for currently running triggers.

Endpoints:
- GET  /api/agents                      -> list all agents with status
- GET  /api/agents/{agent_key}/logs     -> recent logs for a specific agent
- GET  /api/agents/{agent_key}/sources  -> crawl sources for an agent
"""

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentUser, get_current_user, get_agent_log_repository
from app.models.agent_log import AgentLog
from app.models.run_trigger import RunTrigger
from app.models.run import Run
from app.models.source import Source
from app.repositories.agent_log_repository import AgentLogRepository
from app.utils.logger import logger

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


def _read_ndjson_from_file(log_file: Path, limit: int = 500) -> tuple[list[dict], int]:
    """Read NDJSON log file, returning (entries, total_lines)."""
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
    return entries, total_lines


@router.get("")
async def list_agents(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
    log_repo: AgentLogRepository = Depends(get_agent_log_repository),
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

    # For running triggers, check filesystem (process is alive, dirs exist)
    for trigger_id in running_trigger_ids:
        trigger_log_dir = LOG_DIR / trigger_id
        if trigger_log_dir.is_dir():
            for child in trigger_log_dir.iterdir():
                if child.is_dir():
                    running_agents.add(child.name)

    # Count enabled sources per agent type (include shared sources: user_id=0)
    stmt = (
        select(Source.agent_type, func.count())
        .where(or_(Source.user_id == user.id, Source.user_id == 0))
        .where(Source.is_enabled == True)  # noqa: E712
        .group_by(Source.agent_type)
    )
    result = await db.execute(stmt)
    source_counts = dict(result.all())

    # Find recent triggers with logs — query DB first, supplement with filesystem
    agent_triggers: dict[str, list[dict]] = {k: [] for k in AGENT_DEFINITIONS}

    # Get recent triggers from DB
    stmt = (
        select(RunTrigger.run_trigger_id, RunTrigger.status, RunTrigger.created_at)
        .join(Run, RunTrigger.run_id == Run.id)
        .where(Run.user_id == user.id)
        .order_by(RunTrigger.created_at.desc())
        .limit(50)
    )
    result = await db.execute(stmt)
    recent_triggers = result.all()
    trigger_info = {
        tid: (status, created_at) for tid, status, created_at in recent_triggers
    }
    trigger_ids = list(trigger_info.keys())

    # Check DB for which agents have logs for these triggers (resilient)
    seen_pairs: set[tuple[str, str]] = set()
    try:
        db_trigger_agents = await log_repo.get_trigger_agent_map(user.id, trigger_ids)
        for trigger_id, agent_key in db_trigger_agents:
            if agent_key not in agent_triggers:
                continue
            if len(agent_triggers[agent_key]) >= 10:
                continue
            pair = (trigger_id, agent_key)
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            status, created_at = trigger_info.get(trigger_id, (None, None))
            agent_triggers[agent_key].append(
                {
                    "trigger_id": trigger_id,
                    "trigger_status": status,
                    "created_at": created_at.isoformat() if created_at else None,
                }
            )
    except Exception as exc:
        logger.warning("agent_log_db_query_failed err=%s", str(exc)[:200])

    # Supplement with filesystem for triggers not yet in DB
    for trigger_id, status, created_at in recent_triggers:
        trigger_log_dir = LOG_DIR / trigger_id
        if not trigger_log_dir.is_dir():
            continue
        for child in sorted(trigger_log_dir.iterdir()):
            if not child.is_dir():
                continue
            agent_name = child.name
            pair = (trigger_id, agent_name)
            if pair in seen_pairs:
                continue
            if agent_name in agent_triggers and len(agent_triggers[agent_name]) < 10:
                log_file = child / "logs.ndjson"
                if log_file.exists():
                    seen_pairs.add(pair)
                    agent_triggers[agent_name].append(
                        {
                            "trigger_id": trigger_id,
                            "trigger_status": status,
                            "created_at": (
                                created_at.isoformat() if created_at else None
                            ),
                        }
                    )

    agents = []
    for key, defn in AGENT_DEFINITIONS.items():
        agents.append(
            {
                "key": key,
                "label": defn["label"],
                "description": defn["description"],
                "status": "running" if key in running_agents else "idle",
                "sources_count": source_counts.get(key, 0),
                "recent_triggers": agent_triggers.get(key, []),
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
    log_repo: AgentLogRepository = Depends(get_agent_log_repository),
):
    """
    GET /api/agents/{agent_key}/logs
    Auth: Bearer token required.
    Response: { agent_key, trigger_id, total_lines, entries[] }.

    Reads from DB first, falls back to filesystem for running/unpersisted triggers.
    If found on filesystem but not in DB, persists to DB (write-through cache).
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
        # Check DB first (resilient)
        trigger_id = None
        try:
            db_logs = await log_repo.get_triggers_for_agent(user.id, agent_key, limit=1)
            if db_logs:
                trigger_id = db_logs[0].trigger_id
        except Exception:
            pass

        if not trigger_id:
            # Fallback: check filesystem
            stmt = (
                select(RunTrigger.run_trigger_id)
                .join(Run, RunTrigger.run_id == Run.id)
                .where(Run.user_id == user.id)
                .order_by(RunTrigger.created_at.desc())
                .limit(20)
            )
            result = await db.execute(stmt)
            recent = result.all()

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

    # Try DB first (resilient)
    try:
        db_record = await log_repo.get_for_trigger(trigger_id, agent_key)
        if db_record and db_record.entries:
            entries = db_record.entries[:limit]
            return {
                "agent_key": agent_key,
                "trigger_id": trigger_id,
                "total_lines": db_record.total_lines,
                "entries": entries,
            }
    except Exception:
        pass

    # Fallback: read from filesystem
    log_file = LOG_DIR / trigger_id / agent_key / "logs.ndjson"
    if not log_file.exists():
        return {
            "agent_key": agent_key,
            "trigger_id": trigger_id,
            "total_lines": 0,
            "entries": [],
        }

    entries, total_lines = _read_ndjson_from_file(log_file, limit)

    # Write-through cache: persist to DB for future reads after deploy
    try:
        all_entries, all_lines = _read_ndjson_from_file(log_file, limit=10000)
        await log_repo.upsert(
            AgentLog(
                user_id=user.id,
                trigger_id=trigger_id,
                agent_key=agent_key,
                entries=all_entries,
                total_lines=all_lines,
            )
        )
    except Exception:
        pass  # Non-fatal: log will be persisted by orchestrator on completion

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
    Includes shared sources (user_id=0) alongside user-specific sources.
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
        .where(or_(Source.user_id == user.id, Source.user_id == 0))
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
