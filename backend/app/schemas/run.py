"""Pydantic schemas for Run API responses."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.run import RunStatus


class RunResponse(BaseModel):
    """Schema for run API responses."""
    id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: RunStatus
    agent_statuses: Optional[dict] = None
    total_findings: int
    error_log: Optional[str] = None
    triggered_by: str

    model_config = {"from_attributes": True}


class RunTriggerResponse(BaseModel):
    """Schema for run trigger response."""
    run_id: str
    message: str
    status: RunStatus
