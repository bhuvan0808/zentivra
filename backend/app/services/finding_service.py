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
        *,
        category: str | None = None,
        min_confidence: float | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Sequence[Finding]:
        return await self.repo.get_all_filtered(
            category=category,
            min_confidence=min_confidence,
            page=page,
            page_size=page_size,
        )

    async def get_by_uuid(self, finding_id: str) -> Finding:
        finding = await self.repo.get_by_uuid(finding_id)
        if not finding:
            raise HTTPException(status_code=404, detail="Finding not found")
        return finding

    async def get_stats(self) -> dict:
        return await self.repo.get_stats()
