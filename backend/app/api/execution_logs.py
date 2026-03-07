"""Execution Logs API - Preview and download per-agent NDJSON logs for a trigger."""

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from app.dependencies import get_current_user

router = APIRouter(
    prefix="/run-triggers",
    tags=["Execution Logs"],
    dependencies=[Depends(get_current_user)],
)

# Resolved log directory (relative to backend/)
LOG_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "logs"

# Fields to strip from preview (per requirement: skip filename & line number)
_STRIP_FIELDS = {"filename", "lineno", "line_number", "file_name", "pathname"}


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
async def list_trigger_logs(trigger_id: str):
    """List available agent logs for a trigger execution."""
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
):
    """Preview the first N log lines for a specific agent as JSON.

    Strips filename/lineno fields from each log entry per requirement.
    """
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
                    # Strip filename/lineno fields
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
async def download_trigger_log(trigger_id: str, agent_name: str):
    """Download the raw .ndjson log file for a specific agent."""
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
