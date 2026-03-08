"""
Finding model — a single intelligence finding extracted by an agent.

Each finding is a structured piece of intelligence (e.g. competitor update,
benchmark result) pulled from a source URL during a run trigger.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Finding(Base):
    """
    Intelligence finding (table: findings).

    Relationships: run_trigger (lazy=selectin) — the execution that produced this.
    Business rules: src_url is the source page; confidence in [0,1]; category
    for classification (e.g. "announcement", "benchmark").
    """

    __tablename__ = "findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    finding_id: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4())
    )
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    run_trigger_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("run_triggers.id"), nullable=False, index=True
    )
    src_url: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)

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

    run_trigger = relationship("RunTrigger", back_populates="findings", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Finding(finding_id='{self.finding_id}', confidence={self.confidence:.2f})>"

    @property
    def run_trigger_uuid(self) -> str | None:
        """Parent run_trigger's UUID (run_trigger_id) when relationship is loaded."""
        return (
            self.run_trigger.run_trigger_id
            if getattr(self, "run_trigger", None)
            else None
        )
