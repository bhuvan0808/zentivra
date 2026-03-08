"""
DigestSnapshot model — join table linking digests to snapshots.

Many-to-many: a digest can include multiple snapshots; a snapshot can appear
in multiple digests. Used when building digest content from selected sources.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DigestSnapshot(Base):
    """
    Digest–snapshot association (table: digest_snapshots).

    Relationships: digest, snapshot — both use default lazy (select).
    Business rules: each row links one digest to one snapshot; is_enabled
    allows soft-removal from a digest without deleting the link.
    """

    __tablename__ = "digest_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    digest_snapshot_id: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4())
    )
    digest_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("digests.id"), nullable=False, index=True
    )
    snapshot_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("snapshots.id"), nullable=False, index=True
    )

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

    digest = relationship("Digest", back_populates="snapshot_links")
    snapshot = relationship("Snapshot", back_populates="digest_links")

    def __repr__(self) -> str:
        return f"<DigestSnapshot(digest_id={self.digest_id}, snapshot_id={self.snapshot_id})>"
