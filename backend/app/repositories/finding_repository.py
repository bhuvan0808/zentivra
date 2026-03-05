"""Repository for Finding data access."""

from typing import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finding import Finding, FindingCategory
from app.repositories.base import BaseRepository


class FindingRepository(BaseRepository[Finding]):
    def __init__(self, db: AsyncSession):
        super().__init__(Finding, db)

    async def get_all_filtered(
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
        query = select(Finding).order_by(Finding.impact_score.desc())

        if category:
            query = query.where(Finding.category == category)
        if run_id:
            query = query.where(Finding.run_id == run_id)
        if min_confidence is not None:
            query = query.where(Finding.confidence >= min_confidence)
        if min_impact is not None:
            query = query.where(Finding.impact_score >= min_impact)
        if not include_duplicates:
            query = query.where(Finding.is_duplicate == False)  # noqa: E712
        if search:
            query = query.where(
                or_(
                    Finding.title.ilike(f"%{search}%"),
                    Finding.summary_short.ilike(f"%{search}%"),
                )
            )

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_stats(self, run_id: str | None = None) -> dict:
        """Aggregate stats, consistently filtered by run_id when provided."""
        base_filter = [Finding.is_duplicate == False]  # noqa: E712
        if run_id:
            base_filter.append(Finding.run_id == run_id)

        result = await self.db.execute(
            select(Finding.category, func.count(Finding.id))
            .where(*base_filter)
            .group_by(Finding.category)
        )
        category_counts = {row[0]: row[1] for row in result.all()}

        result = await self.db.execute(
            select(func.count(Finding.id)).where(*base_filter)
        )
        total = result.scalar() or 0

        result = await self.db.execute(
            select(func.avg(Finding.impact_score)).where(*base_filter)
        )
        avg_impact = result.scalar() or 0

        return {
            "total_findings": total,
            "by_category": category_counts,
            "avg_impact_score": round(float(avg_impact), 3),
        }
