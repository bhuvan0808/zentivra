"""Pydantic schemas for Source API requests and responses."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl

from app.models.source import AgentType


class SourceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    agent_type: AgentType
    url: str
    feed_url: Optional[str] = None
    css_selectors: Optional[dict] = None
    keywords: Optional[list[str]] = None
    rate_limit_rpm: int = Field(default=10, ge=1, le=120)
    crawl_depth: int = Field(default=1, ge=1, le=5)
    enabled: bool = True


class SourceCreate(SourceBase):
    """Schema for creating a new source."""

    pass


class SourceUpdate(BaseModel):
    """Schema for updating a source (all fields optional)."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    url: Optional[str] = None
    feed_url: Optional[str] = None
    css_selectors: Optional[dict] = None
    keywords: Optional[list[str]] = None
    rate_limit_rpm: Optional[int] = Field(None, ge=1, le=120)
    crawl_depth: Optional[int] = Field(None, ge=1, le=5)
    enabled: Optional[bool] = None


class SourceResponse(SourceBase):
    """Schema for source API responses."""

    id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
