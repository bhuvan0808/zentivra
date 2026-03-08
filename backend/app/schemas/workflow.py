"""
Pydantic schemas for ad-hoc workflow triggers.

Defines request/response schemas for one-off workflows:
- Disruptive article report: DisruptiveArticleRequest -> DisruptiveArticleResponse
  (POST /workflows/disruptive-article or similar endpoint)
"""

from typing import Optional

from pydantic import BaseModel, Field

from app.models.source import AgentType


class DisruptiveArticleRequest(BaseModel):
    """
    Request body for triggering a disruptive article analysis workflow.

    Submits a URL for analysis; optionally restricts agent types and sets a custom title.
    """

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
    """
    Response after triggering a disruptive article report workflow.

    Includes report_id, findings count, email status, PDF paths, and agents used.
    """

    report_id: str
    findings_count: int
    email_sent: bool
    pdf_path: Optional[str] = None
    pdf_download_url: Optional[str] = None
    agents_used: list[AgentType]
    message: str
