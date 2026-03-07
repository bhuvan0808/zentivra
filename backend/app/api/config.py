"""Config API - View and update orchestrator configuration."""

from fastapi import APIRouter, Depends, File, UploadFile

from app.dependencies import get_current_user, get_orchestrator_config_service
from app.schemas.orchestrator_config import OrchestratorConfigResponse
from app.services.orchestrator_config_service import OrchestratorConfigService

router = APIRouter(
    prefix="/config", tags=["Config"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/", response_model=OrchestratorConfigResponse)
async def get_config(
    service: OrchestratorConfigService = Depends(get_orchestrator_config_service),
):
    """Get the current orchestrator configuration with defaults filled in."""
    return await service.get_config()


@router.put("/", response_model=OrchestratorConfigResponse)
async def update_config(
    data: dict,
    service: OrchestratorConfigService = Depends(get_orchestrator_config_service),
):
    """Update orchestrator configuration from a JSON body."""
    return await service.update_config(data)


@router.post("/upload", response_model=OrchestratorConfigResponse)
async def upload_config(
    file: UploadFile = File(...),
    service: OrchestratorConfigService = Depends(get_orchestrator_config_service),
):
    """Upload a .json or .yaml/.yml config file."""
    content = (await file.read()).decode("utf-8")
    filename = file.filename or "config.json"
    ext = filename.rsplit(".", 1)[-1] if "." in filename else "json"
    return await service.update_from_file(content, ext)
