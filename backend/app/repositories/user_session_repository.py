"""
Repository for UserSession model.

Handles session CRUD and bulk operations: lookup by auth token, list active
sessions for a user, deactivate single session or all sessions for a user.
"""

from typing import Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_session import UserSession
from app.repositories.base import BaseRepository


class UserSessionRepository(BaseRepository[UserSession]):
    """
    Thin data-access layer for UserSession model.

    Provides session lookup by token, active-session listing, and
    deactivation (single or bulk) for logout flows.
    """

    uuid_column = "user_session_id"

    def __init__(self, db: AsyncSession):
        super().__init__(UserSession, db)

    async def get_by_token(self, auth_token: str) -> UserSession | None:
        """Lookup session by auth token. Returns None if not found."""
        result = await self.db.execute(
            select(UserSession).where(UserSession.auth_token == auth_token)
        )
        return result.scalar_one_or_none()

    async def get_active_for_user(self, user_id: int) -> Sequence[UserSession]:
        """
        Fetch all active sessions for a user, newest first.

        Filters by user_id and is_active=True, ordered by login_at desc.
        """
        result = await self.db.execute(
            select(UserSession)
            .where(
                UserSession.user_id == user_id, UserSession.is_active == True
            )  # noqa: E712
            .order_by(UserSession.login_at.desc())
        )
        return result.scalars().all()

    async def deactivate(self, session: UserSession, logout_at) -> None:
        """Mark a single session as inactive and set logout_at timestamp."""
        session.is_active = False
        session.logout_at = logout_at
        await self.db.flush()

    async def deactivate_all_for_user(self, user_id: int, logout_at) -> list[str]:
        """
        Deactivate all active sessions for a user via bulk update.

        Returns the list of auth tokens that were deactivated (for invalidation).
        """
        active = await self.get_active_for_user(user_id)
        tokens = [s.auth_token for s in active]
        if tokens:
            await self.db.execute(
                update(UserSession)
                .where(
                    UserSession.user_id == user_id, UserSession.is_active == True
                )  # noqa: E712
                .values(is_active=False, logout_at=logout_at)
            )
            await self.db.flush()
        return tokens
