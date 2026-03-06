"""Repository for Run data access."""

from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finding import Finding
from app.models.run_agent_log import RunAgentLog
from app.models.run import Run, RunStatus
from app.models.snapshot import Snapshot
from app.models.source import AgentType, Source
from app.repositories.base import BaseRepository


class RunRepository(BaseRepository[Run]):
    def __init__(self, db: AsyncSession):
        super().__init__(Run, db)

    async def get_all_filtered(
        self,
        status: RunStatus | None = None,
        limit: int = 20,
    ) -> Sequence[Run]:
        query = select(Run).order_by(Run.started_at.desc()).limit(limit)
        if status:
            query = query.where(Run.status == status)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_running(self) -> Run | None:
        result = await self.db.execute(
            select(Run).where(Run.status == RunStatus.RUNNING)
        )
        return result.scalar_one_or_none()

    async def get_agent_summaries(self, run_id: str) -> list[dict]:
        """Return per-agent run summaries derived from run status + DB activity."""
        run = await self.get_by_id(run_id)
        if not run:
            return []

        status_map = run.agent_statuses or {}

        snapshot_rows = await self.db.execute(
            select(
                Source.agent_type,
                func.count(Snapshot.id),
                func.max(Snapshot.fetched_at),
            )
            .join(Source, Snapshot.source_id == Source.id)
            .where(Snapshot.run_id == run_id)
            .group_by(Source.agent_type)
        )
        snapshots_by_agent = {
            AgentType(row[0]): {"urls_crawled": int(row[1]), "last_activity_at": row[2]}
            for row in snapshot_rows.all()
        }

        finding_rows = await self.db.execute(
            select(Source.agent_type, func.count(Finding.id))
            .join(Source, Finding.source_id == Source.id)
            .where(Finding.run_id == run_id)
            .group_by(Source.agent_type)
        )
        findings_by_agent = {row[0]: int(row[1]) for row in finding_rows.all()}
        findings_by_agent = {
            AgentType(agent_type): count
            for agent_type, count in findings_by_agent.items()
        }

        summaries: list[dict] = []
        for agent_type in AgentType:
            snapshot_info = snapshots_by_agent.get(
                agent_type, {"urls_crawled": 0, "last_activity_at": None}
            )
            summaries.append(
                {
                    "agent_type": agent_type,
                    "status": status_map.get(agent_type.value, "pending"),
                    "findings_count": findings_by_agent.get(agent_type, 0),
                    "urls_crawled": snapshot_info["urls_crawled"],
                    "last_activity_at": snapshot_info["last_activity_at"],
                }
            )
        return summaries

    async def get_agent_activity(
        self, run_id: str, agent_type: AgentType, limit: int = 200
    ) -> list[dict]:
        """Return recent crawl events (snapshots) for an agent within a run."""
        rows = await self.db.execute(
            select(
                Source.name,
                Snapshot.url,
                Snapshot.http_status,
                Snapshot.content_changed,
                Snapshot.fetched_at,
            )
            .join(Source, Snapshot.source_id == Source.id)
            .where(Snapshot.run_id == run_id)
            .where(Source.agent_type == agent_type)
            .order_by(Snapshot.fetched_at.desc())
            .limit(limit)
        )

        return [
            {
                "source_name": row[0],
                "url": row[1],
                "http_status": row[2],
                "content_changed": row[3],
                "fetched_at": row[4],
            }
            for row in rows.all()
        ]

    async def get_agent_logs(
        self, run_id: str, agent_type: AgentType, limit: int = 300
    ) -> list[dict]:
        """Return latest execution logs for one agent in a run."""
        rows = await self.db.execute(
            select(
                RunAgentLog.id,
                RunAgentLog.agent_type,
                RunAgentLog.level,
                RunAgentLog.message,
                RunAgentLog.context,
                RunAgentLog.created_at,
            )
            .where(RunAgentLog.run_id == run_id)
            .where(RunAgentLog.agent_type == agent_type)
            .order_by(RunAgentLog.created_at.desc())
            .limit(limit)
        )

        logs = [
            {
                "id": row[0],
                "agent_type": row[1],
                "level": row[2],
                "message": row[3],
                "context": row[4],
                "created_at": row[5],
            }
            for row in rows.all()
        ]
        logs.reverse()
        return logs
