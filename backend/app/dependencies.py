"""
FastAPI dependency injection chain: db -> repository -> service.

Wires database sessions, repositories, and services for each domain (source, run,
finding, digest, auth). Auth dependencies extract Bearer tokens and validate via
AuthService (Valkey-backed session cache for fast lookups).
"""

from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.repositories.source_repository import SourceRepository
from app.repositories.run_repository import RunRepository
from app.repositories.run_trigger_repository import RunTriggerRepository
from app.repositories.finding_repository import FindingRepository
from app.repositories.digest_repository import DigestRepository
from app.repositories.user_repository import UserRepository
from app.repositories.user_session_repository import UserSessionRepository
from app.services.source_service import SourceService
from app.services.run_service import RunService
from app.services.finding_service import FindingService
from app.services.digest_service import DigestService
from app.services.auth_service import AuthService


@dataclass
class CurrentUser:
    """
    Lightweight authenticated user for route dependencies.

    id: users.id (PK) - used as FK in data tables (sources, runs, etc.)
    user_id: users.user_id (UUID) - external identifier for API responses
    """

    id: int
    user_id: str


# ── Source (db -> repo -> service) ──────────────────────────────────────────


def get_source_repository(db: AsyncSession = Depends(get_db)) -> SourceRepository:
    return SourceRepository(db)


def get_source_service(
    repo: SourceRepository = Depends(get_source_repository),
) -> SourceService:
    return SourceService(repo)


# ── Run (db -> repo -> service) ────────────────────────────────────────────


def get_run_repository(db: AsyncSession = Depends(get_db)) -> RunRepository:
    return RunRepository(db)


def get_run_trigger_repository(
    db: AsyncSession = Depends(get_db),
) -> RunTriggerRepository:
    return RunTriggerRepository(db)


def get_run_service(
    repo: RunRepository = Depends(get_run_repository),
    trigger_repo: RunTriggerRepository = Depends(get_run_trigger_repository),
) -> RunService:
    return RunService(repo, trigger_repo)


# ── Finding (db -> repo -> service) ────────────────────────────────────────


def get_finding_repository(db: AsyncSession = Depends(get_db)) -> FindingRepository:
    return FindingRepository(db)


def get_finding_service(
    repo: FindingRepository = Depends(get_finding_repository),
) -> FindingService:
    return FindingService(repo)


# ── Digest (db -> repo -> service) ─────────────────────────────────────────


def get_digest_repository(db: AsyncSession = Depends(get_db)) -> DigestRepository:
    return DigestRepository(db)


def get_digest_service(
    repo: DigestRepository = Depends(get_digest_repository),
) -> DigestService:
    return DigestService(repo)


# ── Auth (db -> user repo + session repo -> auth service) ───────────────────


def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_user_session_repository(
    db: AsyncSession = Depends(get_db),
) -> UserSessionRepository:
    return UserSessionRepository(db)


def get_auth_service(
    repo: UserRepository = Depends(get_user_repository),
    session_repo: UserSessionRepository = Depends(get_user_session_repository),
) -> AuthService:
    return AuthService(repo, session_repo)


async def get_current_user(
    authorization: str = Header(..., alias="Authorization"),
    service: AuthService = Depends(get_auth_service),
) -> CurrentUser:
    """
    Auth dependency: extract Bearer token, validate via AuthService, return CurrentUser.

    Auth flow: parse Authorization header -> validate_token (Valkey cache, then DB) ->
    return CurrentUser. No DB hit when token is cached in Valkey.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Invalid authorization header format"
        )

    token = authorization[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Missing auth token")

    user = await service.validate_token(token)
    return CurrentUser(id=user.id, user_id=user.user_id)


async def get_current_user_full(
    authorization: str = Header(..., alias="Authorization"),
    service: AuthService = Depends(get_auth_service),
) -> User:
    """
    Auth dependency: extract Bearer token and return full User model.

    Used for /me and other endpoints that need full user profile (email, name, etc.).
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Invalid authorization header format"
        )

    token = authorization[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Missing auth token")

    return await service.validate_token(token)


# ── Workflow (stateless service, no DB dependency) ────────────────────────


def get_workflow_service():
    from app.services.workflow_service import WorkflowService

    return WorkflowService()
