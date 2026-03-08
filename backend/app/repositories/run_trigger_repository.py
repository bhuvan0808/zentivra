"""
Repository for RunTrigger model.

RunTrigger represents an execution instance of a Run. Provides queries with
relationship loading (selectinload) to avoid N+1 queries when accessing
run, findings, snapshots, and digests.
"""

from typing import Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.run_trigger import RunTrigger
from app.models.snapshot import Snapshot
from app.repositories.base import BaseRepository


class RunTriggerRepository(BaseRepository[RunTrigger]):
    """
    Thin data-access layer for RunTrigger model.

    Uses selectinload for eager loading of relationships (run, findings,
    snapshots, digests) to avoid N+1 queries when traversing related data.
    """

    uuid_column = "run_trigger_id"

    def __init__(self, db: AsyncSession):
        super().__init__(RunTrigger, db)

    async def get_by_uuid(self, uuid_str: str) -> RunTrigger | None:
        """
        Lookup trigger by UUID with full relationship loading.

        Eager loads: run, findings, snapshots (with snapshot.source), digests.
        selectinload is used for one-to-many/many relationships to fetch
        related rows in separate efficient queries.
        """
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
        """
        Fetch triggers for a run with relationship loading.

        Eager loads: run, findings, snapshots, digests. Ordered by created_at
        desc, limited to limit rows.
        """
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
        """
        Mark all triggers for a run that are currently is_latest=True as False.

        Used before inserting a new trigger so only the newest remains latest.
        """
        await self.db.execute(
            update(RunTrigger)
            .where(
                RunTrigger.run_id == run_id, RunTrigger.is_latest == True
            )  # noqa: E712
            .values(is_latest=False)
        )
        await self.db.flush()
