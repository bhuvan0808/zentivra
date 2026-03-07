"""Repository for RunTrigger (execution) data access."""

from typing import Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.run_trigger import RunTrigger
from app.models.snapshot import Snapshot
from app.repositories.base import BaseRepository


class RunTriggerRepository(BaseRepository[RunTrigger]):
    uuid_column = "run_trigger_id"

    def __init__(self, db: AsyncSession):
        super().__init__(RunTrigger, db)

    async def get_by_uuid(self, uuid_str: str) -> RunTrigger | None:
        result = await self.db.execute(
            select(RunTrigger)
            .where(RunTrigger.run_trigger_id == uuid_str)
            .options(
                selectinload(RunTrigger.run),
                selectinload(RunTrigger.findings),
                selectinload(RunTrigger.snapshots).selectinload(Snapshot.source),
                selectinload(RunTrigger.digests),
            )
        )
        return result.scalar_one_or_none()

    async def get_triggers_for_run(
        self, run_id: int, *, limit: int = 50
    ) -> Sequence[RunTrigger]:
        result = await self.db.execute(
            select(RunTrigger)
            .where(RunTrigger.run_id == run_id)
            .options(
                selectinload(RunTrigger.run),
                selectinload(RunTrigger.findings),
                selectinload(RunTrigger.snapshots),
                selectinload(RunTrigger.digests),
            )
            .order_by(RunTrigger.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def mark_previous_not_latest(self, run_id: int) -> None:
        await self.db.execute(
            update(RunTrigger)
            .where(RunTrigger.run_id == run_id, RunTrigger.is_latest == True)  # noqa: E712
            .values(is_latest=False)
        )
        await self.db.flush()
