"""Service layer for Source business logic."""

from typing import Sequence

from fastapi import HTTPException

from app.models.source import AgentType, Source
from app.repositories.source_repository import SourceRepository
from app.schemas.source import SourceCreate, SourceUpdate


class SourceService:
    def __init__(self, repo: SourceRepository):
        self.repo = repo

    async def list_sources(
        self,
        agent_type: AgentType | None = None,
        enabled: bool | None = None,
    ) -> Sequence[Source]:
        return await self.repo.get_all_filtered(agent_type=agent_type, enabled=enabled)

    async def get_by_id(self, source_id: str) -> Source:
        source = await self.repo.get_by_id(source_id)
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")
        return source

    async def create(self, data: SourceCreate) -> Source:
        source = Source(**data.model_dump())
        return await self.repo.create(source)

    async def update(self, source_id: str, data: SourceUpdate) -> Source:
        source = await self.get_by_id(source_id)
        update_data = data.model_dump(exclude_unset=True)
        return await self.repo.update(source, update_data)

    async def delete(self, source_id: str) -> None:
        source = await self.get_by_id(source_id)
        await self.repo.delete(source)
