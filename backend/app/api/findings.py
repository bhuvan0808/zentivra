"""Findings API - Browse and search intelligence findings."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.finding import Finding, FindingCategory
from app.schemas.finding import FindingResponse

router = APIRouter(prefix="/findings", tags=["Findings"])


@router.get("/", response_model=list[FindingResponse])
async def list_findings(
    category: Optional[FindingCategory] = Query(None),
    run_id: Optional[str] = Query(None),
    min_confidence: Optional[float] = Query(None, ge=0, le=1),
    min_impact: Optional[float] = Query(None, ge=0),
    search: Optional[str] = Query(None),
    include_duplicates: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Browse findings with filters, search, and pagination."""
    query = select(Finding).order_by(Finding.impact_score.desc())

    # Filters
    if category:
        query = query.where(Finding.category == category)
    if run_id:
        query = query.where(Finding.run_id == run_id)
    if min_confidence is not None:
        query = query.where(Finding.confidence >= min_confidence)
    if min_impact is not None:
        query = query.where(Finding.impact_score >= min_impact)
    if not include_duplicates:
        query = query.where(Finding.is_duplicate == False)
    if search:
        search_filter = or_(
            Finding.title.ilike(f"%{search}%"),
            Finding.summary_short.ilike(f"%{search}%"),
        )
        query = query.where(search_filter)

    # Pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/stats")
async def findings_stats(
    run_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get finding statistics (counts by category, avg scores, etc.)."""
    base_query = select(Finding).where(Finding.is_duplicate == False)
    if run_id:
        base_query = base_query.where(Finding.run_id == run_id)

    # Count by category
    result = await db.execute(
        select(Finding.category, func.count(Finding.id))
        .where(Finding.is_duplicate == False)
        .group_by(Finding.category)
    )
    category_counts = {row[0]: row[1] for row in result.all()}

    # Total count
    result = await db.execute(
        select(func.count(Finding.id)).where(Finding.is_duplicate == False)
    )
    total = result.scalar() or 0

    # Average impact score
    result = await db.execute(
        select(func.avg(Finding.impact_score)).where(Finding.is_duplicate == False)
    )
    avg_impact = result.scalar() or 0

    return {
        "total_findings": total,
        "by_category": category_counts,
        "avg_impact_score": round(float(avg_impact), 3),
    }


@router.get("/{finding_id}", response_model=FindingResponse)
async def get_finding(finding_id: str, db: AsyncSession = Depends(get_db)):
    """Get a finding by ID."""
    result = await db.execute(select(Finding).where(Finding.id == finding_id))
    finding = result.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return finding
