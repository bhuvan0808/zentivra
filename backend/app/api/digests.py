"""
Digests API
===========
URL prefix: /api/digests

View and download intelligence digests (HTML/PDF reports). Digests are
generated per trigger and aggregate findings across sources.
All endpoints require authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.dependencies import CurrentUser, get_current_user, get_digest_service
from app.notifications.email_service import EmailService
from app.schemas.digest import DigestResponse
from app.services.digest_service import DigestService
from app.utils.logger import logger

router = APIRouter(prefix="/digests", tags=["Digests"])


class SendEmailRequest(BaseModel):
    digest_ids: list[str]
    recipients: list[str]


class SendEmailResponse(BaseModel):
    sent: int
    failed: int
    details: list[dict]


@router.get("/", response_model=list[DigestResponse])
async def list_digests(
    limit: int = Query(30, ge=1, le=100),
    service: DigestService = Depends(get_digest_service),
    user: CurrentUser = Depends(get_current_user),
):
    """
    GET /api/digests/
    Auth: Bearer token required.
    Query: limit (1-100, default 30).
    Response: list[DigestResponse].
    """
    return await service.list_digests(user.id, limit=limit)


@router.post("/send-email", response_model=SendEmailResponse)
async def send_digest_email(
    payload: SendEmailRequest,
    service: DigestService = Depends(get_digest_service),
    user: CurrentUser = Depends(get_current_user),
):
    """
    POST /api/digests/send-email
    Auth: Bearer token required.
    Body: { digest_ids: [...], recipients: [...] }
    Sends selected digests as PDF attachments via email.
    """
    if not payload.recipients:
        raise HTTPException(status_code=400, detail="No recipients provided")
    if not payload.digest_ids:
        raise HTTPException(status_code=400, detail="No digests selected")

    email_service = EmailService()
    results = []

    for digest_id in payload.digest_ids:
        try:
            digest = await service.get_by_uuid(digest_id, user.id)
            pdf_path = None
            if digest.pdf_path:
                from pathlib import Path

                p = Path(digest.pdf_path)
                if p.exists():
                    pdf_path = str(p)

            subject = f"Zentivra Digest — {digest.digest_name or digest_id[:8]}"
            sent = await email_service.send_digest_email(
                recipients=payload.recipients,
                subject=subject,
                executive_summary="Please find the attached Zentivra AI Radar digest.",
                pdf_path=pdf_path,
            )
            results.append({"digest_id": digest_id, "sent": sent})
        except HTTPException:
            results.append({"digest_id": digest_id, "sent": False, "error": "not found"})
        except Exception as e:
            logger.error("send_digest_email_error digest=%s err=%s", digest_id, str(e))
            results.append({"digest_id": digest_id, "sent": False, "error": str(e)})

    sent_count = sum(1 for r in results if r.get("sent"))
    failed_count = len(results) - sent_count
    return SendEmailResponse(sent=sent_count, failed=failed_count, details=results)


@router.get("/latest", response_model=DigestResponse)
async def get_latest_digest(
    service: DigestService = Depends(get_digest_service),
    user: CurrentUser = Depends(get_current_user),
):
    """
    GET /api/digests/latest
    Auth: Bearer token required.
    Response: DigestResponse (most recent digest).
    """
    return await service.get_latest(user.id)


@router.get("/{digest_id}", response_model=DigestResponse)
async def get_digest(
    digest_id: str,
    service: DigestService = Depends(get_digest_service),
    user: CurrentUser = Depends(get_current_user),
):
    """
    GET /api/digests/{digest_id}
    Auth: Bearer token required.
    Response: DigestResponse.
    """
    return await service.get_by_uuid(digest_id, user.id)


@router.get("/{digest_id}/html")
async def serve_digest_html(
    digest_id: str,
    service: DigestService = Depends(get_digest_service),
    user: CurrentUser = Depends(get_current_user),
):
    """
    GET /api/digests/{digest_id}/html
    Auth: Bearer token required.
    Response: FileResponse (text/html).
    """
    html_path = await service.get_html_path(digest_id, user.id)
    return FileResponse(
        path=str(html_path),
        media_type="text/html",
        filename=f"zentivra_digest_{html_path.stem}.html",
    )


@router.get("/{digest_id}/pdf")
async def download_digest_pdf(
    digest_id: str,
    service: DigestService = Depends(get_digest_service),
    user: CurrentUser = Depends(get_current_user),
):
    """
    GET /api/digests/{digest_id}/pdf
    Auth: Bearer token required.
    Response: FileResponse (application/pdf).
    """
    pdf_path = await service.get_pdf_path(digest_id, user.id)
    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=f"zentivra_digest_{pdf_path.stem}.pdf",
    )
