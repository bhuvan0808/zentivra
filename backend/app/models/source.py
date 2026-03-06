import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AgentType(str, PyEnum):
    COMPETITOR = "competitor"
    MODEL_PROVIDER = "model_provider"
    RESEARCH = "research"
    HF_BENCHMARK = "hf_benchmark"


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4())
    )
    source_name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    agent_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)

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

    def __repr__(self) -> str:
        return f"<Source(source_name='{self.source_name}', agent_type='{self.agent_type}')>"
