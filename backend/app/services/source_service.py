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
        user_id: int,
        agent_type: AgentType | None = None,
        enabled: bool | None = None,
    ) -> Sequence[Source]:
        return await self.repo.get_all_filtered(
            user_id, agent_type=agent_type, enabled=enabled
        )

    async def get_by_uuid(self, source_id: str, user_id: int) -> Source:
        source = await self.repo.get_by_uuid(source_id, user_id=user_id)
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")
        return source

    async def create(self, data: SourceCreate, user_id: int) -> Source:
        source = Source(
            user_id=user_id,
            source_name=data.source_name,
            display_name=data.display_name,
            agent_type=data.agent_type,
            url=data.url,
        )
        return await self.repo.create(source)

    async def update(self, source_id: str, data: SourceUpdate, user_id: int) -> Source:
        source = await self.get_by_uuid(source_id, user_id)
        if source.user_id == 0:
            raise HTTPException(status_code=403, detail="Cannot modify a shared source")
        update_data = data.model_dump(exclude_unset=True)
        return await self.repo.update(source, update_data)

    async def delete(self, source_id: str, user_id: int) -> None:
        source = await self.get_by_uuid(source_id, user_id)
        if source.user_id == 0:
            raise HTTPException(status_code=403, detail="Cannot delete a shared source")
        await self.repo.delete(source)
