"""
Source model — configurable intelligence feed sources per agent type.

Each source is a URL (e.g. competitor blog, research paper site) that agents
crawl to extract findings. agent_type determines which agent processes the source.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AgentType(str, PyEnum):
    """Agent type for routing sources to the appropriate crawler/analyzer."""

    COMPETITOR = "competitor"
    MODEL_PROVIDER = "model_provider"
    RESEARCH = "research"
    HF_BENCHMARK = "hf_benchmark"


class Source(Base):
    """
    Intelligence feed source (table: sources).

    Relationships: snapshots (lazy=selectin) — per-source execution summaries.
    Business rules: source_name is internal key; display_name is user-facing.
    agent_type must match an AgentType value; url is the crawl target.
    """

    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    source_id: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4())
    )
    source_name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    agent_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)

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

    # Relationships: snapshots — per-trigger execution summaries for this source
    snapshots = relationship("Snapshot", back_populates="source", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Source(source_name='{self.source_name}', agent_type='{self.agent_type}')>"
