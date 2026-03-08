"""Repository for Source data access."""

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source import AgentType, Source
from app.repositories.base import BaseRepository


class SourceRepository(BaseRepository[Source]):
    uuid_column = "source_id"

    def __init__(self, db: AsyncSession):
        super().__init__(Source, db)

    async def get_all_filtered(
        self,
        user_id: int,
        agent_type: AgentType | None = None,
        enabled: bool | None = None,
    ) -> Sequence[Source]:
        query = (
            select(Source)
            .where(Source.user_id == user_id)
            .order_by(Source.created_at.desc())
        )
        if agent_type:
            query = query.where(Source.agent_type == agent_type)
        if enabled is not None:
            query = query.where(Source.is_enabled == enabled)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_uuid(self, uuid_str: str, user_id: int | None = None) -> Source | None:
        query = select(Source).where(Source.source_id == uuid_str)
        if user_id is not None:
            query = query.where(Source.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
