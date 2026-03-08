"""
Snapshot model — per-source execution summary within a trigger.

One snapshot per (run_trigger, source) pair. Captures raw crawl result, count of
findings extracted, and status. Linked to digests via DigestSnapshot.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Snapshot(Base):
    """
    Per-source execution summary (table: snapshots).

    Relationships: run_trigger, source (lazy=selectin); digest_links (lazy=selectin)
    for digests that include this snapshot. Business rules: one snapshot per
    source per trigger; total_findings = count of findings from this source;
    status = pending|completed|failed.
    """

    __tablename__ = "snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_id: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4())
    )
    run_trigger_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("run_triggers.id"), nullable=False, index=True
    )
    source_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sources.id"), nullable=False, index=True
    )
    total_findings: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")

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

    run_trigger = relationship(
        "RunTrigger", back_populates="snapshots", lazy="selectin"
    )
    source = relationship("Source", back_populates="snapshots", lazy="selectin")
    digest_links = relationship(
        "DigestSnapshot", back_populates="snapshot", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Snapshot(snapshot_id='{self.snapshot_id}', status='{self.status}')>"

    @property
    def run_trigger_uuid(self) -> str | None:
        """Parent run_trigger's UUID (run_trigger_id) when relationship is loaded."""
        return (
            self.run_trigger.run_trigger_id
            if getattr(self, "run_trigger", None)
            else None
        )
