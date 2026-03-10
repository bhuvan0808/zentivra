"""
Repository for DisruptiveReport model.

Provides queries for disruptive article report persistence and retrieval.
"""

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.disruptive_report import DisruptiveReport
from app.repositories.base import BaseRepository


class DisruptiveReportRepository(BaseRepository[DisruptiveReport]):
    """
    Thin data-access layer for DisruptiveReport model.

    Provides user-scoped lookups, report history, and report_id-based
    retrieval for PDF download.
    """

    uuid_column = "report_id"

    def __init__(self, db: AsyncSession):
        super().__init__(DisruptiveReport, db)

    async def get_by_report_id(
        self, report_id: str, user_id: int | None = None
    ) -> DisruptiveReport | None:
        """Lookup report by report_id UUID, optionally scoped to a user."""
        query = select(DisruptiveReport).where(
            DisruptiveReport.report_id == report_id
        )
        if user_id is not None:
            query = query.where(DisruptiveReport.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all_for_user(
        self, user_id: int, limit: int = 20
    ) -> Sequence[DisruptiveReport]:
        """Fetch report history for a user, newest first (without PDF bytes)."""
        result = await self.db.execute(
            select(
                DisruptiveReport.id,
                DisruptiveReport.report_id,
                DisruptiveReport.url,
                DisruptiveReport.title,
                DisruptiveReport.recipient_email,
                DisruptiveReport.findings_count,
                DisruptiveReport.email_sent,
                DisruptiveReport.agents_used,
                DisruptiveReport.executive_summary,
                DisruptiveReport.created_at,
            )
            .where(DisruptiveReport.user_id == user_id)
            .order_by(DisruptiveReport.created_at.desc())
            .limit(limit)
        )
        return result.all()
