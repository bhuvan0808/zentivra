import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RunStatus(str, PyEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
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
    crawl_frequency: Mapped[str | None] = mapped_column(String(50), nullable=True)
    crawl_depth: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    keywords: Mapped[list | None] = mapped_column(JSON, nullable=True)

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

    def __repr__(self) -> str:
        return f"<Run(run_name='{self.run_name}', run_id='{self.run_id}')>"
