"""
Source model - Configurable data sources per agent.

Each source represents a URL/feed that an agent crawls (e.g., a competitor blog,
an arXiv query, a HuggingFace leaderboard page).
"""

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, Text
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AgentType(str, PyEnum):
    COMPETITOR = "competitor"
    MODEL_PROVIDER = "model_provider"
    RESEARCH = "research"
    HF_BENCHMARK = "hf_benchmark"


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    agent_type: Mapped[str] = mapped_column(
        Enum(AgentType, native_enum=False), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    feed_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    css_selectors: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    keywords: Mapped[list | None] = mapped_column(JSON, nullable=True)
    rate_limit_rpm: Mapped[int] = mapped_column(Integer, default=10)
    crawl_depth: Mapped[int] = mapped_column(Integer, default=1)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    snapshots = relationship("Snapshot", back_populates="source", lazy="selectin")
    findings = relationship("Finding", back_populates="source", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Source(name='{self.name}', agent_type='{self.agent_type}')>"
