"""Repository for Source data access."""

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source import AgentType, Source
from app.repositories.base import BaseRepository


class SourceRepository(BaseRepository[Source]):
    def __init__(self, db: AsyncSession):
        super().__init__(Source, db)

    async def get_all_filtered(
        self,
        agent_type: AgentType | None = None,
        enabled: bool | None = None,
    ) -> Sequence[Source]:
        query = select(Source).order_by(Source.created_at.desc())
        if agent_type:
            query = query.where(Source.agent_type == agent_type)
        if enabled is not None:
            query = query.where(Source.enabled == enabled)
        result = await self.db.execute(query)
        return result.scalars().all()
