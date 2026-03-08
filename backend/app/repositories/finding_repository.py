"""
Repository for Finding model.

Provides finding queries with filtering by category, run_trigger_id,
min_confidence, and pagination. Also supports aggregate stats by category.
"""

from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finding import Finding
from app.repositories.base import BaseRepository


class FindingRepository(BaseRepository[Finding]):
    """
    Thin data-access layer for Finding model.

    Provides filtered listing with pagination and aggregate statistics
    (total count, counts by category).
    """

    uuid_column = "finding_id"

    def __init__(self, db: AsyncSession):
        super().__init__(Finding, db)

    async def get_all_filtered(
        self,
        user_id: int,
        *,
        category: str | None = None,
        run_trigger_id: int | None = None,
        min_confidence: float | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Sequence[Finding]:
        """
        Fetch findings for a user with optional filters and pagination.

        Filters: user_id (required), category, run_trigger_id, min_confidence.
        Ordered by created_at desc. Paginated via page and page_size.
        """
        query = (
            select(Finding)
            .where(Finding.user_id == user_id)
            .order_by(Finding.created_at.desc())
        )

        if category:
            query = query.where(Finding.category == category)
        if run_trigger_id is not None:
            query = query.where(Finding.run_trigger_id == run_trigger_id)
        if min_confidence is not None:
            query = query.where(Finding.confidence >= min_confidence)

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_stats(self, user_id: int) -> dict:
        """
        Aggregate finding statistics for a user.

        Returns dict with total_findings and by_category (category -> count).
        """
        result = await self.db.execute(
            select(Finding.category, func.count(Finding.id))
            .where(Finding.user_id == user_id)
            .group_by(Finding.category)
        )
        category_counts = {row[0]: row[1] for row in result.all()}

        total_result = await self.db.execute(
            select(func.count(Finding.id)).where(Finding.user_id == user_id)
        )
        total = total_result.scalar() or 0

        return {
            "total_findings": total,
            "by_category": category_counts,
        }

    async def get_by_uuid(
        self, uuid_str: str, user_id: int | None = None
    ) -> Finding | None:
        """
        Lookup finding by UUID.

        If user_id is provided, restricts to that user's findings.
        If user_id is None, returns any matching finding (admin/unrestricted lookup).
        """
        query = select(Finding).where(Finding.finding_id == uuid_str)
        if user_id is not None:
            query = query.where(Finding.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
