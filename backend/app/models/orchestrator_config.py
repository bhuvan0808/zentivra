"""
OrchestratorConfig model — single-row global config for the orchestrator.

Stores runtime settings (e.g. poll interval, concurrency) as a JSON document.
Typically one row with id="default"; allows future multi-tenant configs.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, String, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class OrchestratorConfig(Base):
    """
    Orchestrator runtime config (table: orchestrator_config).

    Single-row pattern: id="default" for the global config. No relationships.
    Business rules: config is a free-form JSON dict; updated_at tracks changes.
    """

    __tablename__ = "orchestrator_config"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default="default")
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<OrchestratorConfig(updated_at='{self.updated_at}')>"
