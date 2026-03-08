"""
Config API
==========
URL prefix: /api/config

View and update orchestrator configuration (LLM settings, crawl params, etc.).
Supports JSON body updates and file upload (.json, .yaml, .yml).
All endpoints require authentication via router-level dependency.
"""

from fastapi import APIRouter, Depends, File, UploadFile

from app.dependencies import get_current_user, get_orchestrator_config_service
from app.schemas.orchestrator_config import OrchestratorConfigResponse
from app.services.orchestrator_config_service import OrchestratorConfigService

router = APIRouter(
    prefix="/config",
    tags=["Config"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/", response_model=OrchestratorConfigResponse)
async def get_config(
    service: OrchestratorConfigService = Depends(get_orchestrator_config_service),
):
    """
    GET /api/config/
    Auth: Bearer token required.
    Response: OrchestratorConfigResponse (with defaults filled in).
    """
    return await service.get_config()


@router.put("/", response_model=OrchestratorConfigResponse)
async def update_config(
    data: dict,
    service: OrchestratorConfigService = Depends(get_orchestrator_config_service),
):
    """
    PUT /api/config/
    Auth: Bearer token required.
    Body: dict (partial config to merge).
    Response: OrchestratorConfigResponse.
    """
    return await service.update_config(data)


@router.post("/upload", response_model=OrchestratorConfigResponse)
async def upload_config(
    file: UploadFile = File(...),
    service: OrchestratorConfigService = Depends(get_orchestrator_config_service),
):
    """
    POST /api/config/upload
    Auth: Bearer token required.
    Body: multipart file (.json, .yaml, .yml).
    Response: OrchestratorConfigResponse.
    """
    content = (await file.read()).decode("utf-8")
    filename = file.filename or "config.json"
    ext = filename.rsplit(".", 1)[-1] if "." in filename else "json"
    return await service.update_from_file(content, ext)
