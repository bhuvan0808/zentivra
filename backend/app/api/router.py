"""Main API Router - Aggregates all sub-routers."""

from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.sources import router as sources_router
from app.api.runs import router as runs_router
from app.api.run_triggers import router as run_triggers_router
from app.api.findings import router as findings_router
from app.api.digests import router as digests_router
from app.api.execution_logs import router as execution_logs_router
from app.api.dashboard import router as dashboard_router

api_router = APIRouter(prefix="/api")

api_router.include_router(auth_router)
api_router.include_router(sources_router)
api_router.include_router(runs_router)
api_router.include_router(run_triggers_router)
api_router.include_router(findings_router)
api_router.include_router(digests_router)
api_router.include_router(execution_logs_router)
api_router.include_router(dashboard_router)
