"""
Pydantic schemas for Run API requests and responses.

Defines schemas for run configuration and trigger management:
- POST /runs: RunCreate -> RunCreateResponse
- PATCH /runs/{run_id}: RunUpdate -> RunResponse
- GET /runs, GET /runs/{run_id}: RunResponse
- POST /runs/{run_id}/trigger: RunTriggerRequest -> RunTriggerResponse
- GET /runs/{run_id}/triggers: RunTriggerDetailResponse
"""

from datetime import datetime
from typing import Annotated, Any, Literal, Optional, Union

from pydantic import BaseModel, BeforeValidator, Field

from app.models.run import RunStatus


class CrawlFrequency(BaseModel):
    """
    Structured schedule for when a run should execute.

    Used within RunCreate/RunUpdate/RunResponse. Supports daily, weekly, or monthly
    cadence with optional time (UTC) and period specifications.
    """

    frequency: Literal["daily", "weekly", "monthly"]
    time: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="HH:MM in UTC")
    periods: Optional[list[str]] = Field(
        None,
        description=(
            "null for daily. Day abbreviations for weekly (e.g. ['mon','wed']). "
            "Date strings for monthly (e.g. ['1','15','28'])."
        ),
    )


def _coerce_crawl_frequency(v: Any) -> Any:
    """Accept both the new JSON object and legacy pipe-delimited strings."""
    if v is None or isinstance(v, dict):
        return v
    if isinstance(v, CrawlFrequency):
        return v
    if isinstance(v, str):
        parts = v.split("|")
        freq = parts[0]
        time_str = parts[1] if len(parts) > 1 else "00:00"
        periods = None
        if freq in ("weekly", "monthly") and len(parts) > 2:
            candidate = parts[2]
            if "/" not in candidate:
                periods = candidate.split(",")
        return {"frequency": freq, "time": time_str, "periods": periods}
    return v


# Type alias: crawl_frequency accepts CrawlFrequency or legacy string format
FlexibleCrawlFrequency = Annotated[
    Optional[CrawlFrequency], BeforeValidator(_coerce_crawl_frequency)
]


class RunCreate(BaseModel):
    """Request body for creating a run configuration (POST /runs)."""

    run_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    enable_pdf_gen: bool = True
    enable_email_alert: bool = False
    email_recipients: Optional[list[str]] = None
    sources: list[str] = Field(..., min_length=1, description="List of source UUIDs")
    crawl_frequency: FlexibleCrawlFrequency = None
    crawl_depth: int = Field(default=0, ge=0, le=10)
    keywords: Optional[list[str]] = None
    trigger_on_create: bool = Field(
        default=False,
        description="If true, trigger the run immediately after creation.",
    )


class RunUpdate(BaseModel):
    """Request body for updating a run configuration (PATCH /runs/{run_id}). All fields optional."""

    run_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    enable_pdf_gen: Optional[bool] = None
    enable_email_alert: Optional[bool] = None
    email_recipients: Optional[list[str]] = None
    sources: Optional[list[str]] = None
    crawl_frequency: FlexibleCrawlFrequency = None
    crawl_depth: Optional[int] = Field(None, ge=0, le=10)
    keywords: Optional[list[str]] = None
    is_enabled: Optional[bool] = None


class RunResponse(BaseModel):
    """Response schema for run endpoints. Exposes run_id and source_ids as UUIDs, never integer PKs."""

    run_id: str
    run_name: str
    description: Optional[str] = None
    enable_pdf_gen: bool
    enable_email_alert: bool
    email_recipients: Optional[list] = None
    sources: list
    crawl_frequency: FlexibleCrawlFrequency = None
    crawl_depth: int
    keywords: Optional[list] = None
    is_enabled: bool
    has_active_triggers: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RunCreateResponse(RunResponse):
    """
    Response for run creation (POST /runs).

    Extends RunResponse with optional trigger field. When trigger_on_create=true
    was set on creation, trigger contains the RunTriggerResponse for the initial run.
    """

    trigger: Optional["RunTriggerResponse"] = None


# --- Trigger-related schemas ---


class RunTriggerRequest(BaseModel):
    """Optional request body when triggering a run (POST /runs/{run_id}/trigger)."""

    trigger_method: str = Field(
        default="manual", description="manual / scheduler / api"
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


class RunTriggerResponse(BaseModel):
    """Response after successfully triggering a run (POST /runs/{run_id}/trigger)."""

    run_trigger_id: str
    run_id: str
    message: str
    status: str


class RunTriggerDetailResponse(BaseModel):
    """Response for trigger history (GET /runs/{run_id}/triggers). Detailed execution info per trigger."""

    run_trigger_id: str
    run_id: Optional[str] = None
    trigger_method: str
    status: str
    is_latest: bool
    created_at: datetime
    updated_at: datetime
    findings_count: int = 0
    snapshots_count: int = 0
    digest_id: Optional[str] = None
    digest_status: Optional[str] = None
    pdf_url: Optional[str] = None
    html_url: Optional[str] = None

    model_config = {"from_attributes": True}
