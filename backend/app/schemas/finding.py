"""Pydantic schemas for Finding API responses."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class FindingResponse(BaseModel):
    """Schema for finding API responses. Exposes UUIDs, never integer PKs/FKs."""

    finding_id: str
    content: Optional[str] = None
    summary: Optional[str] = None
    run_trigger_id: Optional[str] = Field(None, validation_alias="run_trigger_uuid")
    src_url: str
    category: Optional[str] = None
    confidence: float
    created_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}
