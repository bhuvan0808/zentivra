"""
Sources API
===========
URL prefix: /api/sources

CRUD operations for data sources (URLs, feeds, etc.) used in run configurations.
All endpoints require authentication.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.dependencies import CurrentUser, get_current_user, get_source_service
from app.models.source import AgentType
from app.schemas.source import SourceCreate, SourceResponse, SourceUpdate
from app.services.source_service import SourceService

router = APIRouter(prefix="/sources", tags=["Sources"])


@router.get("/", response_model=list[SourceResponse])
async def list_sources(
    agent_type: Optional[AgentType] = Query(None),
    enabled: Optional[bool] = Query(None),
    service: SourceService = Depends(get_source_service),
    user: CurrentUser = Depends(get_current_user),
):
    """
    GET /api/sources/
    Auth: Bearer token required.
    Query: agent_type (optional), enabled (optional).
    Response: list[SourceResponse].
    """
    return await service.list_sources(user.id, agent_type=agent_type, enabled=enabled)


@router.post("/", response_model=SourceResponse, status_code=201)
async def create_source(
    source_data: SourceCreate,
    service: SourceService = Depends(get_source_service),
    user: CurrentUser = Depends(get_current_user),
):
    """Create a new data source."""
    return await service.create(source_data, user.id)


@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(
    source_id: str,
    service: SourceService = Depends(get_source_service),
    user: CurrentUser = Depends(get_current_user),
):
    """
    GET /api/sources/{source_id}
    Auth: Bearer token required.
    Response: SourceResponse.
    """
    return await service.get_by_uuid(source_id, user.id)


@router.put("/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: str,
    source_data: SourceUpdate,
    service: SourceService = Depends(get_source_service),
    user: CurrentUser = Depends(get_current_user),
):
    """
    PUT /api/sources/{source_id}
    Auth: Bearer token required.
    Body: SourceUpdate.
    Response: SourceResponse.
    """
    return await service.update(source_id, source_data, user.id)


@router.delete("/{source_id}", status_code=204)
async def delete_source(
    source_id: str,
    service: SourceService = Depends(get_source_service),
    user: CurrentUser = Depends(get_current_user),
):
    """
    DELETE /api/sources/{source_id}
    Auth: Bearer token required.
    Response: 204 No Content.
    """
    await service.delete(source_id, user.id)
