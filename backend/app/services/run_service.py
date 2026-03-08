from typing import Sequence
from fastapi import HTTPException
from app.models.run import Run
from app.models.run_trigger import RunTrigger
from app.repositories.run_repository import RunRepository
from app.repositories.run_trigger_repository import RunTriggerRepository
from app.schemas.run import RunCreate, RunUpdate, RunTriggerRequest


class RunService:
    def __init__(self, repo: RunRepository, trigger_repo: RunTriggerRepository):
        self.repo = repo
        self.trigger_repo = trigger_repo

    async def list_runs(self, user_id: int, limit: int = 20) -> Sequence[Run]:
        return await self.repo.get_all_filtered(user_id, limit=limit)

    async def get_by_uuid(self, run_id: str, user_id: int) -> Run:
        run = await self.repo.get_by_uuid(run_id, user_id=user_id)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        return run

    async def create(self, run_data: RunCreate, user_id: int) -> Run:
        run = Run(
            user_id=user_id,
            **run_data.model_dump(exclude={"trigger_on_create"}),
        )
        return await self.repo.create(run)

    async def update(self, run_id: str, run_data: RunUpdate, user_id: int) -> Run:
        run = await self.get_by_uuid(run_id, user_id)
        update_data = run_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(run, key, value)
        await self.repo.db.commit()
        await self.repo.db.refresh(run)
        return run

    async def delete(self, run_id: str, user_id: int) -> None:
        run = await self.get_by_uuid(run_id, user_id)
        await self.repo.delete(run)

    async def trigger(
        self, run_id: str, user_id: int, payload: RunTriggerRequest | None = None
    ) -> tuple[RunTrigger, Run, dict]:
        run = await self.get_by_uuid(run_id, user_id)

        await self.trigger_repo.mark_previous_not_latest(run.id)

        trigger = RunTrigger(
            run_id=run.id,
            trigger_method=payload.trigger_method if payload else "manual",
            status="pending",
            is_latest=True,
        )
        created_trigger = await self.trigger_repo.create(trigger)

        await self.repo.db.commit()
        await self.repo.db.refresh(created_trigger)

        options = payload.model_dump() if payload else {}
        return created_trigger, run, options

    async def get_triggers_for_run(
        self, run_id: str, user_id: int, limit: int = 50
    ) -> Sequence[RunTrigger]:
        run = await self.get_by_uuid(run_id, user_id)
        return await self.trigger_repo.get_triggers_for_run(run.id, limit=limit)
