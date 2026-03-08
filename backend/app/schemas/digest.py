"""
Pydantic schemas for Digest API responses.

Defines response schemas for digest reports:
- GET /digests, GET /digests/{digest_id}: DigestResponse
- GET /runs/{run_id}/triggers/{trigger_id}/digest: DigestResponse
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, computed_field


class DigestResponse(BaseModel):
    """
    Response schema for digest endpoints.

    Exposes digest_id and run_trigger_id as UUIDs (via validation_alias for
    run_trigger_uuid), never integer PKs/FKs. Includes computed_field has_pdf.
    """

    digest_id: str
    digest_name: Optional[str] = None
    run_trigger_id: Optional[str] = Field(None, validation_alias="run_trigger_uuid")
    pdf_path: Optional[str] = None
    html_path: Optional[str] = None
    status: str
    created_at: datetime

    @computed_field
    @property
    def has_pdf(self) -> bool:
        """True if a PDF was generated for this digest (pdf_path is non-empty)."""
        return bool(self.pdf_path)

    model_config = {"from_attributes": True, "populate_by_name": True}
