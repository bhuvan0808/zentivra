"""Main API Router - Aggregates all sub-routers."""

from fastapi import APIRouter

from app.api.sources import router as sources_router
from app.api.runs import router as runs_router
from app.api.findings import router as findings_router
from app.api.digests import router as digests_router
from app.api.workflows import router as workflows_router

api_router = APIRouter(prefix="/api")

api_router.include_router(sources_router)
api_router.include_router(runs_router)
api_router.include_router(findings_router)
api_router.include_router(digests_router)
api_router.include_router(workflows_router)
