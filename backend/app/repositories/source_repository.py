"""
Repository for Source model.

Provides source queries with support for shared sources. Uses the convention
_SHARED_USER_ID = 0: sources with user_id=0 are visible to all users (e.g.
system-provided or default sources). User-specific sources are filtered by
user_id.
"""

from typing import Sequence

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source import AgentType, Source
from app.repositories.base import BaseRepository

# Sources with user_id=0 are shared across all users (system/default sources).
_SHARED_USER_ID = 0


class SourceRepository(BaseRepository[Source]):
    """
    Thin data-access layer for Source model.

    Extends BaseRepository with filtered queries that include both
    user-owned sources and shared sources (user_id=0).
    """

    uuid_column = "source_id"

    def __init__(self, db: AsyncSession):
        super().__init__(Source, db)

    async def get_all_filtered(
        self,
        user_id: int,
        agent_type: AgentType | None = None,
        enabled: bool | None = None,
    ) -> Sequence[Source]:
        """
        Fetch sources for a user, including shared sources (user_id=0).

        Filters: user_id (own + shared), optional agent_type, optional enabled.
        Ordered by created_at desc.
        """
        query = (
            select(Source)
            .where(or_(Source.user_id == user_id, Source.user_id == _SHARED_USER_ID))
            .order_by(Source.created_at.desc())
        )
        if agent_type:
            query = query.where(Source.agent_type == agent_type)
        if enabled is not None:
            query = query.where(Source.is_enabled == enabled)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_uuid(
        self, uuid_str: str, user_id: int | None = None
    ) -> Source | None:
        """
        Lookup source by UUID.

        If user_id is provided, restricts to user's own sources or shared (user_id=0).
        If user_id is None, returns any matching source (admin/unrestricted lookup).
        """
        query = select(Source).where(Source.source_id == uuid_str)
        if user_id is not None:
            query = query.where(
                or_(Source.user_id == user_id, Source.user_id == _SHARED_USER_ID)
            )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
