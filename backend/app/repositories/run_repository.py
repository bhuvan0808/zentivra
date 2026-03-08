"""
Repository for Run model.

Run represents a configuration/definition for an execution. Provides CRUD
and filtered queries by user_id, with optional user-scoped UUID lookup.
"""

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.run import Run
from app.repositories.base import BaseRepository


class RunRepository(BaseRepository[Run]):
    """
    Thin data-access layer for Run model.

    Provides run listing and UUID lookup, optionally scoped by user_id
    for multi-tenant isolation.
    """

    uuid_column = "run_id"

    def __init__(self, db: AsyncSession):
        super().__init__(Run, db)

    async def get_all_filtered(
        self,
        user_id: int,
        limit: int = 20,
    ) -> Sequence[Run]:
        """
        Fetch runs for a user, newest first.

        Filters by user_id, ordered by created_at desc, limited to limit rows.
        """
        query = (
            select(Run)
            .where(Run.user_id == user_id)
            .order_by(Run.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_uuid(
        self, uuid_str: str, user_id: int | None = None
    ) -> Run | None:
        """
        Lookup run by UUID.

        If user_id is provided, restricts to that user's runs.
        If user_id is None, returns any matching run (admin/unrestricted lookup).
        """
        query = select(Run).where(Run.run_id == uuid_str)
        if user_id is not None:
            query = query.where(Run.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
