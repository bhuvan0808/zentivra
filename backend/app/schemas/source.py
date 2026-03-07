"""Pydantic schemas for Source API requests and responses."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.source import AgentType


class SourceCreate(BaseModel):
    """Schema for creating a new source."""

    source_name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=255)
    agent_type: AgentType
    url: str = Field(..., min_length=1)


class SourceUpdate(BaseModel):
    """Schema for updating a source (all fields optional)."""

    source_name: Optional[str] = Field(None, min_length=1, max_length=100)
    display_name: Optional[str] = Field(None, min_length=1, max_length=255)
    agent_type: Optional[AgentType] = None
    url: Optional[str] = None
    is_enabled: Optional[bool] = None


class SourceResponse(BaseModel):
    """Schema for source API responses. Exposes UUID, never integer PK."""

    source_id: str
    source_name: str
    display_name: str
    agent_type: str
    url: str
    is_enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
