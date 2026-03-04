"""Digests API - View and download daily intelligence digests."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.digest import Digest
from app.schemas.digest import DigestResponse

router = APIRouter(prefix="/digests", tags=["Digests"])


@router.get("/", response_model=list[DigestResponse])
async def list_digests(
    limit: int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List all digests, most recent first."""
    query = select(Digest).order_by(Digest.date.desc()).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/latest", response_model=DigestResponse)
async def get_latest_digest(db: AsyncSession = Depends(get_db)):
    """Get the most recent digest."""
    result = await db.execute(
        select(Digest).order_by(Digest.date.desc()).limit(1)
    )
    digest = result.scalar_one_or_none()
    if not digest:
        raise HTTPException(status_code=404, detail="No digests found")
    return digest


@router.get("/{digest_id}", response_model=DigestResponse)
async def get_digest(digest_id: str, db: AsyncSession = Depends(get_db)):
    """Get a digest by ID."""
    result = await db.execute(select(Digest).where(Digest.id == digest_id))
    digest = result.scalar_one_or_none()
    if not digest:
        raise HTTPException(status_code=404, detail="Digest not found")
    return digest


@router.get("/{digest_id}/pdf")
async def download_digest_pdf(digest_id: str, db: AsyncSession = Depends(get_db)):
    """Download the PDF for a digest."""
    result = await db.execute(select(Digest).where(Digest.id == digest_id))
    digest = result.scalar_one_or_none()
    if not digest:
        raise HTTPException(status_code=404, detail="Digest not found")
    if not digest.pdf_path:
        raise HTTPException(status_code=404, detail="PDF not yet generated for this digest")

    from pathlib import Path
    pdf_path = Path(digest.pdf_path)
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found on disk")

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=f"zentivra_digest_{digest.date}.pdf",
    )
