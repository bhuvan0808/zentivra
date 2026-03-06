"""
Snapshot model - Raw content captured from a source URL.

Stores the raw HTML/text fetched from a URL along with its content hash
for change detection.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Snapshot(Base):
    __tablename__ = "snapshots"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    source_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sources.id"), nullable=False, index=True
    )
    run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("runs.id"), nullable=False, index=True
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True  # SHA256 hex digest
    )
    raw_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    http_status: Mapped[int] = mapped_column(Integer, nullable=True)
    content_changed: Mapped[bool | None] = mapped_column(
        default=None  # None = first fetch, True = changed, False = unchanged
    )

    # Relationships
    source = relationship("Source", back_populates="snapshots")
    run = relationship("Run", back_populates="snapshots")
    extraction = relationship(
        "Extraction", back_populates="snapshot", uselist=False, lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Snapshot(url='{self.url[:50]}', changed={self.content_changed})>"
