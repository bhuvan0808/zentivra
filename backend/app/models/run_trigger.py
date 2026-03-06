import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RunTrigger(Base):
    __tablename__ = "run_triggers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_trigger_id: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4())
    )
    run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("runs.id"), nullable=False, index=True
    )
    trigger_method: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    is_latest: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    updated_by: Mapped[str | None] = mapped_column(String(36), nullable=True)

    run = relationship("Run", back_populates="triggers")
    findings = relationship("Finding", back_populates="run_trigger", lazy="selectin")
    snapshots = relationship("Snapshot", back_populates="run_trigger", lazy="selectin")
    digests = relationship("Digest", back_populates="run_trigger", lazy="selectin")

    def __repr__(self) -> str:
        return f"<RunTrigger(run_trigger_id='{self.run_trigger_id}', status='{self.status}')>"
