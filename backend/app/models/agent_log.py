"""
AgentLog model — persists agent execution logs for deployment survivability.

Stores NDJSON log entries as a JSON array per (trigger, agent) combination.
This ensures logs survive Render's ephemeral filesystem across deploys.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, ForeignKey, String, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AgentLog(Base):
    """
    Agent execution log record (table: agent_logs).

    One row per (trigger_id, agent_key) combination. Stores the full NDJSON
    log entries as a JSON array for retrieval after filesystem is wiped.
    """

    __tablename__ = "agent_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    agent_log_id: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4())
    )
    trigger_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )
    agent_key: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    entries: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    total_lines: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

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

    def __repr__(self) -> str:
        return f"<AgentLog(trigger_id='{self.trigger_id[:8]}', agent_key='{self.agent_key}')>"
