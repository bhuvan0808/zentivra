"""Pydantic schemas for Finding API responses."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.finding import FindingCategory


class FindingResponse(BaseModel):
    """Schema for finding API responses."""
    id: str
    run_id: str
    source_id: str
    title: str
    date_detected: datetime
    source_url: str
    publisher: Optional[str] = None
    category: FindingCategory
    summary_short: Optional[str] = None
    summary_long: Optional[str] = None
    why_it_matters: Optional[str] = None
    evidence: Optional[dict] = None
    confidence: float
    tags: Optional[list[str]] = None
    entities: Optional[dict] = None
    impact_score: float
    is_duplicate: bool
    cluster_id: Optional[str] = None

    model_config = {"from_attributes": True}


class FindingFilters(BaseModel):
    """Query filters for browsing findings."""
    category: Optional[FindingCategory] = None
    min_confidence: Optional[float] = None
    min_impact: Optional[float] = None
    search: Optional[str] = None
    run_id: Optional[str] = None
    is_duplicate: Optional[bool] = False  # Default: hide duplicates
    page: int = 1
    page_size: int = 20
