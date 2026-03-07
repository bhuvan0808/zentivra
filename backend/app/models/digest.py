"""
Digest model - A compiled intelligence digest.

Matches the actual DB schema: digests table.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Digest(Base):
    __tablename__ = "digests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    digest_id: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4())
    )
    run_trigger_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("run_triggers.id"), nullable=False, index=True
    )
    pdf_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    html_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    digest_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

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

    # Relationships
    run_trigger = relationship("RunTrigger", back_populates="digests", lazy="selectin")
    snapshot_links = relationship(
        "DigestSnapshot", back_populates="digest", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Digest(digest_id='{self.digest_id}', status='{self.status}')>"

    @property
    def run_trigger_uuid(self) -> str | None:
        return (
            self.run_trigger.run_trigger_id
            if getattr(self, "run_trigger", None)
            else None
        )
