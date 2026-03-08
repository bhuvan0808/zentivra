"""
Pydantic schemas for Finding API responses.

Defines response schemas for AI-generated findings:
- GET /findings, GET /findings/{finding_id}: FindingResponse
- GET /runs/{run_id}/triggers/{trigger_id}/findings: FindingResponse
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class FindingResponse(BaseModel):
    """
    Response schema for finding endpoints.

    Exposes finding_id and run_trigger_id as UUIDs (via validation_alias for
    run_trigger_uuid), never integer PKs/FKs. Used when listing or fetching findings.
    """

    finding_id: str
    content: Optional[str] = None
    summary: Optional[str] = None
    run_trigger_id: Optional[str] = Field(None, validation_alias="run_trigger_uuid")
    src_url: str
    category: Optional[str] = None
    confidence: float
    created_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}
