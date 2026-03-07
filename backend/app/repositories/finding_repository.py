"""Repository for Finding data access."""

from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finding import Finding
from app.repositories.base import BaseRepository


class FindingRepository(BaseRepository[Finding]):
    uuid_column = "finding_id"

    def __init__(self, db: AsyncSession):
        super().__init__(Finding, db)

    async def get_all_filtered(
        self,
        *,
        category: str | None = None,
        run_trigger_id: int | None = None,
        min_confidence: float | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Sequence[Finding]:
        query = select(Finding).order_by(Finding.created_at.desc())

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

    async def get_stats(self) -> dict:
        result = await self.db.execute(
            select(Finding.category, func.count(Finding.id)).group_by(Finding.category)
        )
        category_counts = {row[0]: row[1] for row in result.all()}

        total_result = await self.db.execute(select(func.count(Finding.id)))
        total = total_result.scalar() or 0

        return {
            "total_findings": total,
            "by_category": category_counts,
        }
