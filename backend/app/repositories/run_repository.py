"""Repository for Run (configuration) data access."""

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.run import Run
from app.repositories.base import BaseRepository


class RunRepository(BaseRepository[Run]):
    uuid_column = "run_id"

    def __init__(self, db: AsyncSession):
        super().__init__(Run, db)

    async def get_all_filtered(
        self,
        user_id: int,
        limit: int = 20,
    ) -> Sequence[Run]:
        query = (
            select(Run)
            .where(Run.user_id == user_id)
            .order_by(Run.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_uuid(self, uuid_str: str, user_id: int | None = None) -> Run | None:
        query = select(Run).where(Run.run_id == uuid_str)
        if user_id is not None:
            query = query.where(Run.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
