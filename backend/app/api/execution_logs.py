"""
Execution Logs API
==================
URL prefix: /api/run-triggers (shared with run_triggers router)

Preview and download per-agent NDJSON logs for a trigger execution. Logs are
stored under data/logs/{trigger_id}/{agent_name}/logs.ndjson.
All endpoints require authentication.
"""

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentUser, get_current_user
from app.repositories.run_trigger_repository import RunTriggerRepository

router = APIRouter(
    prefix="/run-triggers",
    tags=["Execution Logs"],
)

LOG_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "logs"

_STRIP_FIELDS = {"filename", "lineno", "line_number", "file_name", "pathname"}


async def _verify_trigger_ownership(
    trigger_id: str, db: AsyncSession, user: CurrentUser
) -> None:
    """Verify the trigger belongs to a run owned by the current user."""
    repo = RunTriggerRepository(db)
    trigger = await repo.get_by_uuid(trigger_id)
    if not trigger:
        raise HTTPException(status_code=404, detail="Run trigger not found")
    if trigger.run and trigger.run.user_id != user.id:
        raise HTTPException(status_code=404, detail="Run trigger not found")


def _trigger_log_dir(trigger_id: str) -> Path:
    """Return the log directory for a trigger, validating it exists."""
    p = LOG_DIR / trigger_id
    if not p.is_dir():
        raise HTTPException(
            status_code=404,
            detail=f"No logs found for trigger {trigger_id}",
        )
    return p


def _count_lines(file_path: Path) -> int:
    """Count lines in a file efficiently."""
    count = 0
    with open(file_path, "r", encoding="utf-8") as f:
        for _ in f:
            count += 1
    return count


@router.get("/{trigger_id}/logs")
async def list_trigger_logs(
    trigger_id: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """
    GET /api/run-triggers/{trigger_id}/logs
    Auth: Bearer token required.
    Response: list[{agent_name, file_size, line_count}].
    """
    await _verify_trigger_ownership(trigger_id, db, user)
    log_dir = _trigger_log_dir(trigger_id)

    agents = []
    for child in sorted(log_dir.iterdir()):
        if not child.is_dir():
            continue
        log_file = child / "logs.ndjson"
        if not log_file.exists():
            continue
        agents.append(
            {
                "agent_name": child.name,
                "file_size": log_file.stat().st_size,
                "line_count": _count_lines(log_file),
            }
        )

    return agents


@router.get("/{trigger_id}/logs/{agent_name}/preview")
async def preview_trigger_logs(
    trigger_id: str,
    agent_name: str,
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Preview the first N log lines for a specific agent as JSON."""
    await _verify_trigger_ownership(trigger_id, db, user)
    log_dir = _trigger_log_dir(trigger_id)
    log_file = log_dir / agent_name / "logs.ndjson"

    if not log_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"No logs found for agent '{agent_name}' in trigger {trigger_id}",
        )

    preview: list[dict] = []
    total_lines = 0

    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            total_lines += 1
            if len(preview) < limit:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    for field in _STRIP_FIELDS:
                        entry.pop(field, None)
                    preview.append(entry)
                except json.JSONDecodeError:
                    continue

    return {
        "agent_name": agent_name,
        "total_lines": total_lines,
        "preview": preview,
    }


@router.get("/{trigger_id}/logs/{agent_name}/download")
async def download_trigger_log(
    trigger_id: str,
    agent_name: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """
    GET /api/run-triggers/{trigger_id}/logs/{agent_name}/download
    Auth: Bearer token required.
    Response: FileResponse (application/x-ndjson).
    """
    await _verify_trigger_ownership(trigger_id, db, user)
    log_dir = _trigger_log_dir(trigger_id)
    log_file = log_dir / agent_name / "logs.ndjson"

    if not log_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"No logs found for agent '{agent_name}' in trigger {trigger_id}",
        )

    short_id = trigger_id[:8]
    return FileResponse(
        path=str(log_file),
        media_type="application/x-ndjson",
        filename=f"{short_id}_{agent_name}.ndjson",
    )
