"""Service layer for Run business logic."""

from datetime import datetime, timezone
from typing import Sequence

from fastapi import HTTPException

from app.config import settings
from app.models.run import Run, RunStatus
from app.models.source import AgentType
from app.repositories.run_repository import RunRepository
from app.schemas.run import RunTriggerRequest


class RunService:
    def __init__(self, repo: RunRepository):
        self.repo = repo

    async def list_runs(
        self,
        status: RunStatus | None = None,
        limit: int = 20,
    ) -> Sequence[Run]:
        return await self.repo.get_all_filtered(status=status, limit=limit)

    async def get_by_id(self, run_id: str) -> Run:
        run = await self.repo.get_by_id(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        return run

    async def trigger(self, payload: RunTriggerRequest | None = None) -> tuple[Run, dict]:
        existing = await self.repo.get_running()
        if existing:
            stale_timeout_seconds = max(0, int(settings.stale_run_timeout_seconds))
            started_at = existing.started_at
            if started_at and started_at.tzinfo is None:
                started_at = started_at.replace(tzinfo=timezone.utc)

            run_age_seconds = (
                (datetime.now(timezone.utc) - started_at).total_seconds()
                if started_at
                else 0
            )
            is_stale = stale_timeout_seconds > 0 and run_age_seconds > stale_timeout_seconds

            if is_stale:
                existing.status = RunStatus.FAILED
                existing.completed_at = datetime.now(timezone.utc)
                statuses = dict(existing.agent_statuses or {})
                for agent_name, status in list(statuses.items()):
                    status_text = str(status)
                    if status_text.startswith("running") or status_text == "pending":
                        statuses[agent_name] = "failed (stale timeout)"
                existing.agent_statuses = statuses
                existing.error_log = (
                    "Automatically marked failed after exceeding stale run timeout "
                    f"({stale_timeout_seconds}s)."
                )
                await self.repo.db.commit()
            else:
                raise HTTPException(
                    status_code=409,
                    detail=f"Run {existing.id} is already in progress.",
                )

        run = Run(triggered_by="manual")
        created = await self.repo.create(run)
        # Ensure the run row is committed before background execution starts.
        await self.repo.db.commit()
        await self.repo.db.refresh(created)
        options = payload.model_dump() if payload else {}
        return created, options

    async def get_agent_summaries(self, run_id: str) -> list[dict]:
        _ = await self.get_by_id(run_id)
        return await self.repo.get_agent_summaries(run_id)

    async def get_agent_activity(
        self, run_id: str, agent_type: AgentType, limit: int = 200
    ) -> list[dict]:
        _ = await self.get_by_id(run_id)
        return await self.repo.get_agent_activity(run_id, agent_type, limit=limit)

    async def get_agent_logs(
        self, run_id: str, agent_type: AgentType, limit: int = 300
    ) -> list[dict]:
        _ = await self.get_by_id(run_id)
        return await self.repo.get_agent_logs(run_id, agent_type, limit=limit)
