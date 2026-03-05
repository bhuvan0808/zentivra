"""Repository for Run data access."""

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.run import Run, RunStatus
from app.repositories.base import BaseRepository


class RunRepository(BaseRepository[Run]):
    def __init__(self, db: AsyncSession):
        super().__init__(Run, db)

    async def get_all_filtered(
        self,
        status: RunStatus | None = None,
        limit: int = 20,
    ) -> Sequence[Run]:
        query = select(Run).order_by(Run.started_at.desc()).limit(limit)
        if status:
            query = query.where(Run.status == status)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_running(self) -> Run | None:
        result = await self.db.execute(
            select(Run).where(Run.status == RunStatus.RUNNING)
        )
        return result.scalar_one_or_none()
