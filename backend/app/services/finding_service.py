"""Service layer for Finding business logic."""

from typing import Sequence

from fastapi import HTTPException

from app.models.finding import Finding
from app.repositories.finding_repository import FindingRepository


class FindingService:
    def __init__(self, repo: FindingRepository):
        self.repo = repo

    async def list_findings(
        self,
        user_id: int,
        *,
        category: str | None = None,
        min_confidence: float | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Sequence[Finding]:
        return await self.repo.get_all_filtered(
            user_id,
            category=category,
            min_confidence=min_confidence,
            page=page,
            page_size=page_size,
        )

    async def get_by_uuid(self, finding_id: str, user_id: int) -> Finding:
        finding = await self.repo.get_by_uuid(finding_id, user_id=user_id)
        if not finding:
            raise HTTPException(status_code=404, detail="Finding not found")
        return finding

    async def get_stats(self, user_id: int) -> dict:
        return await self.repo.get_stats(user_id)
