"""Sources API - CRUD operations for data sources."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.source import AgentType, Source
from app.schemas.source import SourceCreate, SourceResponse, SourceUpdate

router = APIRouter(prefix="/sources", tags=["Sources"])


@router.get("/", response_model=list[SourceResponse])
async def list_sources(
    agent_type: Optional[AgentType] = Query(None),
    enabled: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List all sources, optionally filtered by agent type or enabled status."""
    query = select(Source).order_by(Source.created_at.desc())
    if agent_type:
        query = query.where(Source.agent_type == agent_type)
    if enabled is not None:
        query = query.where(Source.enabled == enabled)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=SourceResponse, status_code=201)
async def create_source(
    source_data: SourceCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new data source."""
    source = Source(**source_data.model_dump())
    db.add(source)
    await db.flush()
    await db.refresh(source)
    return source


@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(source_id: str, db: AsyncSession = Depends(get_db)):
    """Get a source by ID."""
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source


@router.put("/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: str,
    source_data: SourceUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a source."""
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    update_data = source_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(source, field, value)

    await db.flush()
    await db.refresh(source)
    return source


@router.delete("/{source_id}", status_code=204)
async def delete_source(source_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a source."""
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    await db.delete(source)
