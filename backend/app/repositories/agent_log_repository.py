"""
Repository for AgentLog model.

Provides queries for agent log persistence and retrieval,
supporting the write-through cache pattern from filesystem to DB.
"""

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_log import AgentLog
from app.repositories.base import BaseRepository


class AgentLogRepository(BaseRepository[AgentLog]):
    """
    Thin data-access layer for AgentLog model.

    Provides trigger-based lookups and upsert for the write-through
    cache pattern (filesystem -> DB persistence).
    """

    uuid_column = "agent_log_id"

    def __init__(self, db: AsyncSession):
        super().__init__(AgentLog, db)

    async def get_for_trigger(
        self, trigger_id: str, agent_key: str
    ) -> AgentLog | None:
        """Lookup log entries for a specific trigger + agent combination."""
        result = await self.db.execute(
            select(AgentLog)
            .where(AgentLog.trigger_id == trigger_id)
            .where(AgentLog.agent_key == agent_key)
        )
        return result.scalar_one_or_none()

    async def get_triggers_for_agent(
        self, user_id: int, agent_key: str, limit: int = 10
    ) -> Sequence[AgentLog]:
        """Fetch recent log records for a specific agent, newest first."""
        result = await self.db.execute(
            select(AgentLog)
            .where(AgentLog.user_id == user_id)
            .where(AgentLog.agent_key == agent_key)
            .order_by(AgentLog.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_trigger_agent_map(
        self, user_id: int, trigger_ids: list[str]
    ) -> list[tuple]:
        """
        Get lightweight (trigger_id, agent_key) pairs for given triggers.

        Used by list_agents to determine which agents have logs for which triggers.
        """
        if not trigger_ids:
            return []
        result = await self.db.execute(
            select(AgentLog.trigger_id, AgentLog.agent_key)
            .where(AgentLog.user_id == user_id)
            .where(AgentLog.trigger_id.in_(trigger_ids))
        )
        return result.all()

    async def upsert(self, agent_log: AgentLog) -> AgentLog:
        """Insert or update an agent log record (write-through cache)."""
        existing = await self.get_for_trigger(
            agent_log.trigger_id, agent_log.agent_key
        )
        if existing:
            existing.entries = agent_log.entries
            existing.total_lines = agent_log.total_lines
            await self.db.flush()
            await self.db.refresh(existing)
            return existing
        return await self.create(agent_log)
