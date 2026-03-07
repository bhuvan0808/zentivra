"""Pydantic schemas for Digest API responses."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DigestResponse(BaseModel):
    """Schema for digest API responses. Exposes UUIDs, never integer PKs/FKs."""

    digest_id: str
    digest_name: Optional[str] = None
    run_trigger_id: Optional[str] = Field(
        None, validation_alias="run_trigger_uuid"
    )
    pdf_path: Optional[str] = None
    html_path: Optional[str] = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}
