"""
Finding queries and statistics service.

This module encapsulates business logic for findings (agent-extracted insights):
listing with filters (category, confidence), pagination, and aggregate statistics.
Findings are read-only from the agent perspective; no create/update/delete.
"""

from typing import Sequence

from fastapi import HTTPException

from app.models.finding import Finding
from app.repositories.finding_repository import FindingRepository


class FindingService:
    """
    Orchestrates FindingRepository for finding queries and stats.

    Applies business rules (user scoping), raises HTTPExceptions for not-found.
    No side effects; read-only operations.
    """

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
        """
        List findings for a user with optional filters and pagination.

        Filters: category, minimum confidence. Results are paginated.
        """
        return await self.repo.get_all_filtered(
            user_id,
            category=category,
            min_confidence=min_confidence,
            page=page,
            page_size=page_size,
        )

    async def get_by_uuid(self, finding_id: str, user_id: int) -> Finding:
        """
        Fetch a finding by UUID, scoped to user.

        Raises:
            HTTPException 404: Finding not found.
        """
        finding = await self.repo.get_by_uuid(finding_id, user_id=user_id)
        if not finding:
            raise HTTPException(status_code=404, detail="Finding not found")
        return finding

    async def get_stats(self, user_id: int) -> dict:
        """
        Return aggregate statistics for the user's findings.

        Typically includes counts by category, confidence distribution, etc.
        """
        return await self.repo.get_stats(user_id)
