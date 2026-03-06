"""Pydantic schemas for Run API responses."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.run import RunStatus
from app.models.source import AgentType


class RunTriggerRequest(BaseModel):
    """Optional payload for manually triggering a run."""

    agent_types: Optional[list[AgentType]] = Field(
        default=None,
        description="Optional subset of agents to execute.",
    )
    source_ids: Optional[list[str]] = Field(
        default=None,
        description="Optional subset of enabled source IDs to crawl.",
    )
    recipients: Optional[list[str]] = Field(
        default=None,
        description="Optional override for email recipients for this run only.",
    )
    max_sources_per_agent: Optional[int] = Field(
        default=None,
        ge=1,
        le=50,
        description="Optional cap to keep test runs small/cost-controlled.",
    )


class RunResponse(BaseModel):
    """Schema for run API responses."""

    id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: RunStatus
    agent_statuses: Optional[dict] = None
    total_findings: int
    error_log: Optional[str] = None
    log_path: Optional[str] = None
    triggered_by: str

    model_config = {"from_attributes": True}


class RunTriggerResponse(BaseModel):
    """Schema for run trigger response."""

    run_id: str
    message: str
    status: RunStatus


class RunAgentSummaryResponse(BaseModel):
    """Per-agent summary for a run."""

    agent_type: AgentType
    status: str
    findings_count: int = 0
    urls_crawled: int = 0
    last_activity_at: Optional[datetime] = None


class RunAgentActivityResponse(BaseModel):
    """Recent URL crawl activity for one agent in a run."""

    source_name: str
    url: str
    http_status: Optional[int] = None
    content_changed: Optional[bool] = None
    fetched_at: datetime


class RunAgentLogResponse(BaseModel):
    """Recent execution log lines for one agent in a run."""

    id: str
    agent_type: AgentType
    level: str
    message: str
    context: Optional[dict] = None
    created_at: datetime
