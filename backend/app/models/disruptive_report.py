"""
DisruptiveReport model — persists oops/disruptive article reports.

Stores report metadata, executive summary, and PDF binary data so reports
survive Render's ephemeral filesystem across deploys.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, DateTime, Integer, ForeignKey, LargeBinary, String, Text, JSON,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DisruptiveReport(Base):
    """
    Disruptive article report record (table: disruptive_reports).

    Stores the full report including PDF bytes for download survivability.
    """

    __tablename__ = "disruptive_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    report_id: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4())
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False)
    findings_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    email_sent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    agents_used: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    executive_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    pdf_data: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)

    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    updated_by: Mapped[str | None] = mapped_column(String(36), nullable=True)

    def __repr__(self) -> str:
        return f"<DisruptiveReport(report_id='{self.report_id[:8]}', findings={self.findings_count})>"
