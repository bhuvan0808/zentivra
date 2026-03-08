"""
Pydantic schemas for Snapshot API responses.

Defines response schemas for per-source snapshots within a run trigger:
- GET /runs/{run_id}/triggers/{trigger_id}/snapshots: SnapshotResponse
- GET /snapshots/{snapshot_id}: SnapshotResponse
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SnapshotResponse(BaseModel):
    """Response schema for snapshot endpoints. Exposes snapshot_id as UUID, never integer PK."""

    snapshot_id: str
    source_name: Optional[str] = None
    total_findings: int = 0
    summary: Optional[str] = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
