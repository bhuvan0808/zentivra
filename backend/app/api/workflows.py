"""Workflow API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.dependencies import get_workflow_service
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
):
    """Generate a one-off article report PDF and send it to a target email."""
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

    return DisruptiveArticleResponse(
        report_id=result["report_id"],
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


@router.get("/reports/{report_id}/pdf")
async def download_disruptive_report_pdf(
    report_id: str,
    service: WorkflowService = Depends(get_workflow_service),
):
    """Download a previously generated disruptive-article PDF report."""
    pdf_path = service.get_disruptive_report_pdf_path(report_id)
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="Report PDF not found")
    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=f"disruptive_article_{report_id}.pdf",
    )
