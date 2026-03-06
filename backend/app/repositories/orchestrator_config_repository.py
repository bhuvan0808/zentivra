"""Repository for the single-row orchestrator config."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orchestrator_config import OrchestratorConfig


class OrchestratorConfigRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self) -> OrchestratorConfig | None:
        result = await self.db.execute(
            select(OrchestratorConfig).where(OrchestratorConfig.id == "default")
        )
        return result.scalar_one_or_none()

    async def upsert(self, config_dict: dict) -> OrchestratorConfig:
        existing = await self.get()
        if existing:
            existing.config = config_dict
            existing.updated_at = datetime.now(timezone.utc)
            await self.db.flush()
            await self.db.refresh(existing)
            return existing

        row = OrchestratorConfig(id="default", config=config_dict)
        self.db.add(row)
        await self.db.flush()
        await self.db.refresh(row)
        return row
