"""
Source CRUD service with shared-source protection.

This module encapsulates business logic for data sources (e.g., feeds, URLs)
that agents crawl. Enforces shared source protection: sources with user_id=0
are system-wide and cannot be modified or deleted by any user.
"""

from typing import Sequence

from fastapi import HTTPException

from app.models.source import AgentType, Source
from app.repositories.source_repository import SourceRepository
from app.schemas.source import SourceCreate, SourceUpdate


class SourceService:
    """
    Orchestrates SourceRepository for source CRUD operations.

    Applies business rules (shared source protection), raises HTTPExceptions
    for not-found and forbidden modifications. All operations are scoped by user_id.
    """

    def __init__(self, repo: SourceRepository):
        self.repo = repo

    async def list_sources(
        self,
        user_id: int,
        agent_type: AgentType | None = None,
        enabled: bool | None = None,
    ) -> Sequence[Source]:
        """
        List sources for a user, optionally filtered by agent type and enabled status.

        Includes shared sources (user_id=0) in results for all users.
        """
        return await self.repo.get_all_filtered(
            user_id, agent_type=agent_type, enabled=enabled
        )

    async def get_by_uuid(self, source_id: str, user_id: int) -> Source:
        """
        Fetch a source by UUID, scoped to user (includes shared sources).

        Raises:
            HTTPException 404: Source not found.
        """
        source = await self.repo.get_by_uuid(source_id, user_id=user_id)
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")
        return source

    async def create(self, data: SourceCreate, user_id: int) -> Source:
        """
        Create a new source owned by the user.

        No validation beyond schema; user_id is always the requesting user.
        """
        source = Source(
            user_id=user_id,
            source_name=data.source_name,
            display_name=data.display_name,
            agent_type=data.agent_type,
            url=data.url,
        )
        return await self.repo.create(source)

    async def update(self, source_id: str, data: SourceUpdate, user_id: int) -> Source:
        """
        Update a source. Shared sources (user_id=0) cannot be modified.

        Raises:
            HTTPException 403: Cannot modify a shared source.
            HTTPException 404: Source not found.
        """
        source = await self.get_by_uuid(source_id, user_id)
        if source.user_id == 0:
            raise HTTPException(status_code=403, detail="Cannot modify a shared source")
        update_data = data.model_dump(exclude_unset=True)
        return await self.repo.update(source, update_data)

    async def delete(self, source_id: str, user_id: int) -> None:
        """
        Delete a source. Shared sources (user_id=0) cannot be deleted.

        Raises:
            HTTPException 403: Cannot delete a shared source.
            HTTPException 404: Source not found.
        """
        source = await self.get_by_uuid(source_id, user_id)
        if source.user_id == 0:
            raise HTTPException(status_code=403, detail="Cannot delete a shared source")
        await self.repo.delete(source)
