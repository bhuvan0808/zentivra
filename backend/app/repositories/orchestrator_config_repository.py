"""
Repository for OrchestratorConfig model.

Implements a single-row config pattern: the table holds exactly one row
(id="default") that stores global orchestrator configuration as JSON.
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orchestrator_config import OrchestratorConfig


class OrchestratorConfigRepository:
    """
    Thin data-access layer for OrchestratorConfig (single-row pattern).

    Does not extend BaseRepository because config is a singleton: one row
    with id="default". Provides get and upsert (create-or-update).
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self) -> OrchestratorConfig | None:
        """
        Fetch the single orchestrator config row (id="default").

        Returns None if the config has not been created yet.
        """
        result = await self.db.execute(
            select(OrchestratorConfig).where(OrchestratorConfig.id == "default")
        )
        return result.scalar_one_or_none()

    async def upsert(self, config_dict: dict) -> OrchestratorConfig:
        """
        Create or update the single orchestrator config row.

        If a row exists, updates its config dict and updated_at.
        Otherwise inserts a new row with id="default".
        """
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
