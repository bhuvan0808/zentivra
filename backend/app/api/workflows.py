"""
Workflows API
=============
URL prefix: /api/workflows

One-off analysis workflows (e.g. disruptive article report). These endpoints
run ad-hoc pipelines outside the scheduled run/trigger model. Reports are
persisted to DB for survivability across Render deploys.

Endpoints:
- POST /api/workflows/disruptive-article       -> generate report
- GET  /api/workflows/reports                   -> report history
- GET  /api/workflows/reports/{report_id}/pdf   -> download PDF
"""

from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from app.dependencies import (
    CurrentUser,
    get_current_user,
    get_disruptive_report_repository,
    get_workflow_service,
)
from app.models.disruptive_report import DisruptiveReport
from app.repositories.disruptive_report_repository import DisruptiveReportRepository
from app.schemas.workflow import (
    DisruptiveArticleRequest,
    DisruptiveArticleResponse,
)
from app.services.workflow_service import WorkflowService

router = APIRouter(prefix="/workflows", tags=["Workflows"])


@router.post(
    "/disruptive-article",
    response_model=DisruptiveArticleResponse,
)
async def disruptive_article_workflow(
    payload: DisruptiveArticleRequest,
    service: WorkflowService = Depends(get_workflow_service),
    report_repo: DisruptiveReportRepository = Depends(get_disruptive_report_repository),
    user: CurrentUser = Depends(get_current_user),
):
    """Generate a one-off article report PDF, persist to DB, and email it."""
    try:
        result = await service.disruptive_article_report(
            url=payload.url,
            recipient_email=payload.recipient_email,
            agent_types=payload.agent_types,
            title=payload.title,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow failed: {e}")

    report_id = result["report_id"]
    pdf_path = result.get("pdf_path")
    download_url = (
        f"/api/workflows/reports/{report_id}/pdf"
        if pdf_path and str(pdf_path).endswith(".pdf")
        else None
    )

    # Persist report to DB for survivability across deploys
    try:
        agents_used_values = [
            a.value if hasattr(a, "value") else str(a)
            for a in result.get("agents_used", [])
        ]
        report = DisruptiveReport(
            user_id=user.id,
            report_id=report_id,
            url=payload.url,
            title=payload.title,
            recipient_email=payload.recipient_email,
            findings_count=result.get("findings_count", 0),
            email_sent=result.get("email_sent", False),
            agents_used=agents_used_values,
            executive_summary=result.get("executive_summary", ""),
            pdf_data=result.get("pdf_bytes"),
        )
        await report_repo.create(report)
    except Exception:
        pass  # Non-fatal: report was still generated and emailed

    return DisruptiveArticleResponse(
        report_id=report_id,
        findings_count=result["findings_count"],
        email_sent=result["email_sent"],
        pdf_path=pdf_path,
        pdf_download_url=download_url,
        agents_used=result["agents_used"],
        message=(
            "Report generated and email sent."
            if result["email_sent"]
            else "Report generated, but email was not sent (check SMTP config)."
        ),
    )


@router.get("/reports")
async def list_reports(
    report_repo: DisruptiveReportRepository = Depends(get_disruptive_report_repository),
    user: CurrentUser = Depends(get_current_user),
):
    """
    GET /api/workflows/reports
    Auth: Bearer token required.
    Response: list of past disruptive article reports (without PDF bytes).
    """
    rows = await report_repo.get_all_for_user(user.id, limit=20)
    return [
        {
            "report_id": row.report_id,
            "url": row.url,
            "title": row.title,
            "recipient_email": row.recipient_email,
            "findings_count": row.findings_count,
            "email_sent": row.email_sent,
            "agents_used": row.agents_used,
            "executive_summary": (row.executive_summary or "")[:300],
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "pdf_download_url": f"/api/workflows/reports/{row.report_id}/pdf",
        }
        for row in rows
    ]


@router.get("/reports/{report_id}/pdf")
async def download_disruptive_report_pdf(
    report_id: str,
    report_repo: DisruptiveReportRepository = Depends(get_disruptive_report_repository),
    service: WorkflowService = Depends(get_workflow_service),
):
    """
    GET /api/workflows/reports/{report_id}/pdf
    Auth: None (public download link, report_id UUID acts as capability token).
    Response: PDF file stream.

    Tries filesystem first (for recently generated reports), falls back to DB.
    """
    # Try filesystem first
    pdf_path = service.get_disruptive_report_pdf_path(report_id)
    if pdf_path.exists():
        return FileResponse(
            path=str(pdf_path),
            media_type="application/pdf",
            filename=f"disruptive_article_{report_id}.pdf",
        )

    # Fallback: serve from DB
    report = await report_repo.get_by_report_id(report_id)
    if not report or not report.pdf_data:
        raise HTTPException(status_code=404, detail="Report PDF not found")

    return StreamingResponse(
        BytesIO(report.pdf_data),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="disruptive_article_{report_id}.pdf"'
        },
    )
