"""Pydantic schemas for Snapshot API responses."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SnapshotResponse(BaseModel):
    """Schema for snapshot API responses. Exposes UUIDs."""

    snapshot_id: str
    source_name: Optional[str] = None
    total_findings: int = 0
    summary: Optional[str] = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
