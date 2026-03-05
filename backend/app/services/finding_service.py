"""Service layer for Finding business logic."""

from typing import Sequence

from fastapi import HTTPException

from app.models.finding import Finding, FindingCategory
from app.repositories.finding_repository import FindingRepository


class FindingService:
    def __init__(self, repo: FindingRepository):
        self.repo = repo

    async def list_findings(
        self,
        *,
        category: FindingCategory | None = None,
        run_id: str | None = None,
        min_confidence: float | None = None,
        min_impact: float | None = None,
        search: str | None = None,
        include_duplicates: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> Sequence[Finding]:
        return await self.repo.get_all_filtered(
            category=category,
            run_id=run_id,
            min_confidence=min_confidence,
            min_impact=min_impact,
            search=search,
            include_duplicates=include_duplicates,
            page=page,
            page_size=page_size,
        )

    async def get_by_id(self, finding_id: str) -> Finding:
        finding = await self.repo.get_by_id(finding_id)
        if not finding:
            raise HTTPException(status_code=404, detail="Finding not found")
        return finding

    async def get_stats(self, run_id: str | None = None) -> dict:
        return await self.repo.get_stats(run_id=run_id)
