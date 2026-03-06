"""
OrchestratorConfig model - Single-row table storing the orchestrator's
runtime configuration as a JSON document.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, String, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class OrchestratorConfig(Base):
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
