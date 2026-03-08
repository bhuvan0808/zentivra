"""Repository for Digest data access."""

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.digest import Digest
from app.repositories.base import BaseRepository


class DigestRepository(BaseRepository[Digest]):
    uuid_column = "digest_id"

    def __init__(self, db: AsyncSession):
        super().__init__(Digest, db)

    async def get_all_ordered(self, user_id: int, limit: int = 30) -> Sequence[Digest]:
        query = (
            select(Digest)
            .where(Digest.user_id == user_id)
            .order_by(Digest.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_latest(self, user_id: int) -> Digest | None:
        result = await self.db.execute(
            select(Digest)
            .where(Digest.user_id == user_id)
            .order_by(Digest.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_uuid(self, uuid_str: str, user_id: int | None = None) -> Digest | None:
        query = select(Digest).where(Digest.digest_id == uuid_str)
        if user_id is not None:
            query = query.where(Digest.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
