"""Schemas for ad-hoc workflows (e.g., disruptive article reports)."""

from typing import Optional

from pydantic import BaseModel, Field

from app.models.source import AgentType


class DisruptiveArticleRequest(BaseModel):
    """Request payload for one-off disruptive article analysis."""

    url: str = Field(..., min_length=5)
    recipient_email: str = Field(..., min_length=5)
    agent_types: Optional[list[AgentType]] = Field(
        default=None,
        description="Optional subset of agents to analyze the article.",
    )
    title: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Optional custom title for the generated report.",
    )


class DisruptiveArticleResponse(BaseModel):
    """Response for disruptive article report generation."""

    report_id: str
    findings_count: int
    email_sent: bool
    pdf_path: Optional[str] = None
    pdf_download_url: Optional[str] = None
    agents_used: list[AgentType]
    message: str
