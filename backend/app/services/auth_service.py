"""
Authentication service with Valkey-first session caching.

This module encapsulates all auth business logic: signup, login, logout, and token
validation. Uses Valkey as the primary session store for fast token validation
(cache hit avoids DB query). Sessions are also persisted in the database for
audit and cross-service consistency.
"""

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

from app.config import settings
from app.core.valkey_client import valkey_client
from app.core.security import generate_auth_token, hash_password, verify_password
from app.models.user import User
from app.models.user_session import UserSession
from app.repositories.user_repository import UserRepository
from app.repositories.user_session_repository import UserSessionRepository
from app.schemas.auth import AuthResponse


def _utcnow() -> datetime:
    """Return current UTC datetime for session expiry and deactivation."""
    return datetime.now(timezone.utc)


class AuthService:
    """
    Orchestrates user and session repositories for authentication.

    Applies business rules (e.g., duplicate username/email, disabled accounts),
    raises HTTPExceptions for invalid credentials or conflicts. Creates and
    invalidates sessions in both Valkey and the database.
    """

    def __init__(self, repo: UserRepository, session_repo: UserSessionRepository):
        self.repo = repo
        self.session_repo = session_repo

    async def signup(
        self, username: str, email: str, password: str, display_name: str
    ) -> AuthResponse:
        """
        Register a new user and create an authenticated session.

        Flow: validate uniqueness -> hash password -> create user -> create session
        -> store session in Valkey. Returns auth token and user info.

        Raises:
            HTTPException 409: Username or email already taken.
        """
        existing_username = await self.repo.get_by_username(username)
        if existing_username:
            raise HTTPException(status_code=409, detail="Username already taken")

        existing_email = await self.repo.get_by_email(email)
        if existing_email:
            raise HTTPException(status_code=409, detail="Email already registered")

        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            display_name=display_name,
        )
        user = await self.repo.create(user)

        token, expires_at = await self._create_session(user.id, user.user_id)

        return AuthResponse(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            display_name=user.display_name,
            auth_token=token,
            expires_at=expires_at,
        )

    async def login(self, username_or_email: str, password: str) -> AuthResponse:
        """
        Authenticate user and create a new session.

        Validates credentials, checks account is enabled, then creates session
        and stores in Valkey. Returns auth token and user info.

        Raises:
            HTTPException 401: Invalid credentials.
            HTTPException 403: Account is disabled.
        """
        user = await self.repo.get_by_username_or_email(username_or_email)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not verify_password(password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not user.is_enabled:
            raise HTTPException(status_code=403, detail="Account is disabled")

        token, expires_at = await self._create_session(user.id, user.user_id)

        return AuthResponse(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            display_name=user.display_name,
            auth_token=token,
            expires_at=expires_at,
        )

    async def logout(self, auth_token: str) -> None:
        """
        Invalidate the session for the given token.

        Side effects: deletes from Valkey immediately; deactivates session row
        in DB if it exists. Idempotent for unknown tokens.
        """
        await valkey_client.delete_session(auth_token)

        session = await self.session_repo.get_by_token(auth_token)
        if session:
            await self.session_repo.deactivate(session, _utcnow())

    async def validate_token(self, auth_token: str) -> User:
        """
        Validate auth token and return the associated User.

        Fast path: Valkey cache hit -> fetch user by ID -> no DB session query.
        Slow path: cache miss -> lookup session in DB -> check expiry -> fetch user.
        Side effects: deactivates expired sessions and removes them from Valkey.

        Raises:
            HTTPException 401: Invalid/expired token or session.
            HTTPException 403: Account is disabled.
        """
        cached = await valkey_client.get_session(auth_token)
        if cached:
            user = await self.repo.get_by_id(cached["id"])
            if user and user.is_enabled:
                return user

        session = await self.session_repo.get_by_token(auth_token)
        if not session or not session.is_active:
            raise HTTPException(status_code=401, detail="Invalid or expired session")

        now = _utcnow()
        expires = session.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires < now:
            await self.session_repo.deactivate(session, now)
            await valkey_client.delete_session(auth_token)
            raise HTTPException(status_code=401, detail="Session expired")

        user = await self.repo.get_by_id(session.user_id)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid or expired session")

        if not user.is_enabled:
            raise HTTPException(status_code=403, detail="Account is disabled")

        return user

    async def invalidate_all_sessions(self, user_id: int) -> None:
        """Revoke every active session for a user (password change, account disable)."""
        tokens = await self.session_repo.deactivate_all_for_user(user_id, _utcnow())
        await valkey_client.delete_sessions(tokens)

    async def _create_session(
        self, user_pk: int, user_uuid: str
    ) -> tuple[str, datetime]:
        """
        Create a new session in DB and Valkey.

        Generates token, persists UserSession row, commits DB, then stores
        session in Valkey with TTL for fast validation. Returns (token, expires_at).
        """
        now = _utcnow()
        ttl_hours = settings.auth_token_ttl_hours
        token = generate_auth_token()
        expires_at = now + timedelta(hours=ttl_hours)

        session = UserSession(
            user_id=user_pk,
            auth_token=token,
            login_at=now,
            expires_at=expires_at,
            is_active=True,
        )
        await self.session_repo.create(session)
        await self.session_repo.db.commit()

        await valkey_client.create_session(
            user_pk=user_pk,
            user_uuid=user_uuid,
            session_id=session.user_session_id,
            auth_token=token,
            ttl_seconds=ttl_hours * 3600,
            expires_at=expires_at.isoformat(),
        )

        return token, expires_at
