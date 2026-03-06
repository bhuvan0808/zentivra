"""
Digest model - A compiled daily intelligence digest.

Stores the executive summary, PDF path, and email delivery status
for each generated daily report.
"""

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Digest(Base):
    __tablename__ = "digests"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("runs.id"), nullable=False, unique=True, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    executive_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    pdf_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    email_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    recipients: Mapped[list | None] = mapped_column(JSON, nullable=True)
    sections: Mapped[dict | None] = mapped_column(
        JSON, nullable=True  # Per-section narratives for the digest
    )
    total_findings: Mapped[int | None] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    run = relationship("Run", back_populates="digest")

    def __repr__(self) -> str:
        return f"<Digest(date='{self.date}', email_sent={self.email_sent})>"
