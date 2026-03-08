"""
Repository for User model.

Provides user lookups by username, email, UUID, or a generic identifier
(username or email). Used for authentication and user resolution.
"""

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    Thin data-access layer for User model.

    Extends BaseRepository with domain-specific lookups for login
    and user resolution (username, email, or either).
    """

    uuid_column = "user_id"

    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_username(self, username: str) -> User | None:
        """Lookup user by unique username. Returns None if not found."""
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Lookup user by unique email. Returns None if not found."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_username_or_email(self, identifier: str) -> User | None:
        """
        Lookup user by username or email.

        Accepts a single identifier string and matches against either field.
        Useful for login forms where the user may enter either.
        """
        result = await self.db.execute(
            select(User).where(
                or_(User.username == identifier, User.email == identifier)
            )
        )
        return result.scalar_one_or_none()
