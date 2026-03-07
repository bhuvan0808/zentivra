"""Sources API - CRUD operations for data sources."""

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_current_user, get_source_service
from app.models.source import AgentType
from app.schemas.source import SourceCreate, SourceResponse, SourceUpdate
from app.services.source_service import SourceService

router = APIRouter(
    prefix="/sources", tags=["Sources"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/", response_model=list[SourceResponse])
async def list_sources(
    agent_type: Optional[AgentType] = Query(None),
    enabled: Optional[bool] = Query(None),
    service: SourceService = Depends(get_source_service),
):
    """List all sources, optionally filtered by agent type or enabled status."""
    return await service.list_sources(agent_type=agent_type, enabled=enabled)


@router.post("/", response_model=SourceResponse, status_code=201)
async def create_source(
    source_data: SourceCreate,
    service: SourceService = Depends(get_source_service),
):
    """Create a new data source."""
    return await service.create(source_data)


@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(
    source_id: str,
    service: SourceService = Depends(get_source_service),
):
    """Get a source by its UUID."""
    return await service.get_by_uuid(source_id)


@router.put("/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: str,
    source_data: SourceUpdate,
    service: SourceService = Depends(get_source_service),
):
    """Update a source by its UUID."""
    return await service.update(source_id, source_data)


@router.delete("/{source_id}", status_code=204)
async def delete_source(
    source_id: str,
    service: SourceService = Depends(get_source_service),
):
    """Delete a source by its UUID."""
    await service.delete(source_id)
