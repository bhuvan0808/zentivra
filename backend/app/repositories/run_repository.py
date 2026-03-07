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
        limit: int = 20,
    ) -> Sequence[Run]:
        query = (
            select(Run)
            .order_by(Run.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()
