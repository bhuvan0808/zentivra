"""
RunAgentLog model - Per-agent execution logs captured during a run.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.source import AgentType


class RunAgentLog(Base):
    __tablename__ = "run_agent_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("runs.id"), nullable=False, index=True
    )
    agent_type: Mapped[str] = mapped_column(
        Enum(AgentType, native_enum=False), nullable=False, index=True
    )
    level: Mapped[str] = mapped_column(String(16), default="info", index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    def __repr__(self) -> str:
        return (
            f"<RunAgentLog(run_id='{self.run_id[:8]}', agent='{self.agent_type}', "
            f"level='{self.level}')>"
        )
