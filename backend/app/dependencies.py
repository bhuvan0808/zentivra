"""FastAPI dependency injection chain: db -> repository -> service."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.source_repository import SourceRepository
from app.repositories.run_repository import RunRepository
from app.repositories.finding_repository import FindingRepository
from app.repositories.digest_repository import DigestRepository
from app.services.source_service import SourceService
from app.services.run_service import RunService
from app.services.finding_service import FindingService
from app.services.digest_service import DigestService
from app.services.workflow_service import WorkflowService


# ── Source ──────────────────────────────────────────────

def get_source_repository(db: AsyncSession = Depends(get_db)) -> SourceRepository:
    return SourceRepository(db)


def get_source_service(
    repo: SourceRepository = Depends(get_source_repository),
) -> SourceService:
    return SourceService(repo)


# ── Run ─────────────────────────────────────────────────

def get_run_repository(db: AsyncSession = Depends(get_db)) -> RunRepository:
    return RunRepository(db)


def get_run_service(
    repo: RunRepository = Depends(get_run_repository),
) -> RunService:
    return RunService(repo)


# ── Finding ─────────────────────────────────────────────

def get_finding_repository(db: AsyncSession = Depends(get_db)) -> FindingRepository:
    return FindingRepository(db)


def get_finding_service(
    repo: FindingRepository = Depends(get_finding_repository),
) -> FindingService:
    return FindingService(repo)


# ── Digest ──────────────────────────────────────────────

def get_digest_repository(db: AsyncSession = Depends(get_db)) -> DigestRepository:
    return DigestRepository(db)


def get_digest_service(
    repo: DigestRepository = Depends(get_digest_repository),
) -> DigestService:
    return DigestService(repo)


# ── Workflows ───────────────────────────────────────────

def get_workflow_service() -> WorkflowService:
    return WorkflowService()
