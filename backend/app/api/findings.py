"""
Findings API
=============
URL prefix: /api/findings

Browse and search intelligence findings produced by pipeline runs. Supports
filtering by category and confidence, pagination, and aggregate stats.
All endpoints require authentication.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.dependencies import CurrentUser, get_current_user, get_finding_service
from app.schemas.finding import FindingResponse
from app.services.finding_service import FindingService

router = APIRouter(prefix="/findings", tags=["Findings"])


@router.get("/", response_model=list[FindingResponse])
async def list_findings(
    category: Optional[str] = Query(None),
    min_confidence: Optional[float] = Query(None, ge=0, le=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: FindingService = Depends(get_finding_service),
    user: CurrentUser = Depends(get_current_user),
):
    """
    GET /api/findings/
    Auth: Bearer token required.
    Query: category (optional), min_confidence (0-1, optional), page, page_size.
    Response: list[FindingResponse].
    """
    return await service.list_findings(
        user.id,
        category=category,
        min_confidence=min_confidence,
        page=page,
        page_size=page_size,
    )


@router.get("/stats")
async def findings_stats(
    service: FindingService = Depends(get_finding_service),
    user: CurrentUser = Depends(get_current_user),
):
    """
    GET /api/findings/stats
    Auth: Bearer token required.
    Response: dict with counts by category.
    """
    return await service.get_stats(user.id)


@router.get("/{finding_id}", response_model=FindingResponse)
async def get_finding(
    finding_id: str,
    service: FindingService = Depends(get_finding_service),
    user: CurrentUser = Depends(get_current_user),
):
    """
    GET /api/findings/{finding_id}
    Auth: Bearer token required.
    Response: FindingResponse.
    """
    return await service.get_by_uuid(finding_id, user.id)
