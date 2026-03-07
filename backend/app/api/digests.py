"""Digests API - View and download intelligence digests."""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse

from app.dependencies import get_current_user, get_digest_service
from app.schemas.digest import DigestResponse
from app.services.digest_service import DigestService

router = APIRouter(
    prefix="/digests", tags=["Digests"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/", response_model=list[DigestResponse])
async def list_digests(
    limit: int = Query(30, ge=1, le=100),
    service: DigestService = Depends(get_digest_service),
):
    """List all digests, most recent first."""
    return await service.list_digests(limit=limit)


@router.get("/latest", response_model=DigestResponse)
async def get_latest_digest(
    service: DigestService = Depends(get_digest_service),
):
    """Get the most recent digest."""
    return await service.get_latest()


@router.get("/{digest_id}", response_model=DigestResponse)
async def get_digest(
    digest_id: str,
    service: DigestService = Depends(get_digest_service),
):
    """Get a digest by its UUID."""
    return await service.get_by_uuid(digest_id)


@router.get("/{digest_id}/html")
async def serve_digest_html(
    digest_id: str,
    service: DigestService = Depends(get_digest_service),
):
    """Serve the HTML for a digest."""
    html_path = await service.get_html_path(digest_id)
    return FileResponse(
        path=str(html_path),
        media_type="text/html",
        filename=f"zentivra_digest_{html_path.stem}.html",
    )


@router.get("/{digest_id}/pdf")
async def download_digest_pdf(
    digest_id: str,
    service: DigestService = Depends(get_digest_service),
):
    """Download the PDF for a digest."""
    pdf_path = await service.get_pdf_path(digest_id)
    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=f"zentivra_digest_{pdf_path.stem}.pdf",
    )
