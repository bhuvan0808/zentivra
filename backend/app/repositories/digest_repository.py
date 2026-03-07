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

    async def get_all_ordered(self, limit: int = 30) -> Sequence[Digest]:
        query = select(Digest).order_by(Digest.created_at.desc()).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_latest(self) -> Digest | None:
        result = await self.db.execute(
            select(Digest).order_by(Digest.created_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()
