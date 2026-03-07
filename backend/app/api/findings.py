"""Findings API - Browse and search intelligence findings."""

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_current_user, get_finding_service

from app.schemas.finding import FindingResponse
from app.services.finding_service import FindingService

router = APIRouter(
    prefix="/findings",
    tags=["Findings"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/", response_model=list[FindingResponse])
async def list_findings(
    category: Optional[str] = Query(None),
    min_confidence: Optional[float] = Query(None, ge=0, le=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: FindingService = Depends(get_finding_service),
):
    """Browse findings with filters and pagination."""
    return await service.list_findings(
        category=category,
        min_confidence=min_confidence,
        page=page,
        page_size=page_size,
    )


@router.get("/stats")
async def findings_stats(
    service: FindingService = Depends(get_finding_service),
):
    """Get finding statistics (counts by category)."""
    return await service.get_stats()


@router.get("/{finding_id}", response_model=FindingResponse)
async def get_finding(
    finding_id: str,
    service: FindingService = Depends(get_finding_service),
):
    """Get a finding by its UUID."""
    return await service.get_by_uuid(finding_id)
