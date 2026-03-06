"""
Run model - Represents a single pipeline execution.

Tracks the overall status, per-agent statuses, and timing for each daily run.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, Integer, String, Text
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RunStatus(str, PyEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"  # Some agents failed, but digest was still produced


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(
        Enum(RunStatus, native_enum=False), default=RunStatus.PENDING, index=True
    )
    agent_statuses: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    total_findings: Mapped[int] = mapped_column(Integer, default=0)
    error_log: Mapped[str | None] = mapped_column(Text, nullable=True)
    triggered_by: Mapped[str] = mapped_column(
        String(50), default="scheduler"  # "scheduler" or "manual"
    )

    # Relationships
    snapshots = relationship("Snapshot", back_populates="run", lazy="selectin")
    findings = relationship("Finding", back_populates="run", lazy="selectin")
    digest = relationship("Digest", back_populates="run", uselist=False, lazy="selectin")
    agent_logs = relationship("RunAgentLog", back_populates="run", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Run(id='{self.id[:8]}', status='{self.status}')>"
