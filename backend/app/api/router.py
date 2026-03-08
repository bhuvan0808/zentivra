"""
Central API Router
==================
Mounts all API sub-routers under the /api prefix.

URL prefix: /api

Sub-routers mounted:
- auth: /api/auth (signup, login, logout, me)
- sources: /api/sources (CRUD for data sources)
- runs: /api/runs (CRUD for run configs, trigger endpoint)
- run_triggers: /api/run-triggers (trigger details, findings, snapshots)
- findings: /api/findings (list, stats, get by ID)
- digests: /api/digests (list, latest, HTML/PDF download)
- execution_logs: /api/run-triggers (NDJSON log list, preview, download)
- dashboard: /api/dashboard (KPI, charts, triggers, sources)
"""

from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.sources import router as sources_router
from app.api.runs import router as runs_router
from app.api.run_triggers import router as run_triggers_router
from app.api.findings import router as findings_router
from app.api.digests import router as digests_router
from app.api.execution_logs import router as execution_logs_router
from app.api.dashboard import router as dashboard_router
from app.api.agents_api import router as agents_router
from app.api.workflows import router as workflows_router

api_router = APIRouter(prefix="/api")

api_router.include_router(auth_router)
api_router.include_router(sources_router)
api_router.include_router(runs_router)
api_router.include_router(run_triggers_router)
api_router.include_router(findings_router)
api_router.include_router(digests_router)
api_router.include_router(execution_logs_router)
api_router.include_router(dashboard_router)
api_router.include_router(agents_router)
api_router.include_router(workflows_router)
