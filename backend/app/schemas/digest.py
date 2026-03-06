"""Pydantic schemas for Digest API responses."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class DigestResponse(BaseModel):
    """Schema for digest API responses."""

    id: str
    run_id: str
    date: date
    executive_summary: Optional[str] = None
    pdf_path: Optional[str] = None
    email_sent: bool
    sent_at: Optional[datetime] = None
    recipients: Optional[list[str]] = None
    total_findings: Optional[int] = 0
    created_at: datetime

    model_config = {"from_attributes": True}
