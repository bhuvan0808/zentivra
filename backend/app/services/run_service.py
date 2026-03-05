"""Service layer for Run business logic."""

from typing import Sequence

from fastapi import HTTPException

from app.models.run import Run, RunStatus
from app.repositories.run_repository import RunRepository


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

    async def trigger(self) -> Run:
        existing = await self.repo.get_running()
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Run {existing.id} is already in progress.",
            )
        run = Run(triggered_by="manual")
        return await self.repo.create(run)
