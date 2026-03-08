"""
Run model — crawl configuration and scheduling.

A run defines which sources to crawl, how often, and what outputs to produce
(PDF digest, email alerts). Triggers are individual executions of a run.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RunStatus(str, PyEnum):
    """Status of a run trigger execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class Run(Base):
    """
    Run configuration (table: runs).

    Relationships: triggers (lazy=selectin) — individual executions of this run.
    Business rules: sources is a JSON list of source_ids to crawl; crawl_frequency
    defines schedule (e.g. cron); crawl_depth limits link-following depth.
    """

    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    run_id: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4())
    )
    run_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    enable_pdf_gen: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    enable_email_alert: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    email_recipients: Mapped[list | None] = mapped_column(JSON, nullable=True)
    sources: Mapped[list] = mapped_column(JSON, nullable=False)
    crawl_frequency: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    crawl_depth: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    keywords: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # sources: list of source_ids to include in this run
    # crawl_frequency: schedule config (e.g. {"type": "cron", "expression": "0 9 * * *"})
    # keywords: optional filter terms for relevance

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

    triggers = relationship("RunTrigger", back_populates="run", lazy="selectin")

    @property
    def has_active_triggers(self) -> bool:
        """True if any trigger is pending or running (execution in progress)."""
        if not self.triggers:
            return False
        return any(t.status in ("pending", "running") for t in self.triggers)

    def __repr__(self) -> str:
        return f"<Run(run_name='{self.run_name}', run_id='{self.run_id}')>"
