"""
Finding model - A single intelligence finding produced by an agent.

This is the core data entity: a summarized, scored, categorized piece of
intelligence about AI industry news, research, or benchmarks.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class FindingCategory(str, PyEnum):
    MODELS = "models"
    APIS = "apis"
    PRICING = "pricing"
    BENCHMARKS = "benchmarks"
    SAFETY = "safety"
    TOOLING = "tooling"
    RESEARCH = "research"
    OTHER = "other"


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("runs.id"), nullable=False, index=True
    )
    source_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sources.id"), nullable=False, index=True
    )

    # Core fields from spec
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    date_detected: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    publisher: Mapped[str] = mapped_column(String(255), nullable=True)
    category: Mapped[str] = mapped_column(
        Enum(FindingCategory, native_enum=False), default=FindingCategory.OTHER, index=True
    )

    # Summaries
    summary_short: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary_long: Mapped[str | None] = mapped_column(Text, nullable=True)
    why_it_matters: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Evidence & scoring
    evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    entities: Mapped[dict | None] = mapped_column(
        JSON, nullable=True  # {"companies": [], "models": [], "datasets": []}
    )
    diff_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Ranking
    impact_score: Mapped[float] = mapped_column(Float, default=0.0)
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0)
    novelty_score: Mapped[float] = mapped_column(Float, default=0.0)
    credibility_score: Mapped[float] = mapped_column(Float, default=0.0)
    actionability_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Deduplication
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False)
    cluster_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # Relationships
    run = relationship("Run", back_populates="findings")
    source = relationship("Source", back_populates="findings")

    def __repr__(self) -> str:
        return f"<Finding(title='{self.title[:50]}', impact={self.impact_score:.2f})>"
