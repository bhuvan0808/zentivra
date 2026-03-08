"""
Base repository with generic async CRUD operations.

This module provides BaseRepository, a thin data-access layer that services
can extend for any SQLAlchemy model. It encapsulates common patterns:
get by id/uuid, list with ordering/limit, create, update, and delete.
"""

from typing import Generic, Sequence, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """
    Generic repository providing reusable CRUD for any SQLAlchemy model.

    Acts as a thin data-access layer between service and DB. Subclasses
    set uuid_column to the model's UUID attribute name for API-facing lookups.
    """

    uuid_column: str = ""

    def __init__(self, model: type[ModelT], db: AsyncSession):
        """Initialize with the model class and async database session."""
        self.model = model
        self.db = db

    async def get_by_id(self, entity_id: int) -> ModelT | None:
        """Lookup by integer primary key (internal use only)."""
        result = await self.db.execute(
            select(self.model).where(self.model.id == entity_id)
        )
        return result.scalar_one_or_none()

    async def get_by_uuid(self, uuid_str: str) -> ModelT | None:
        """
        Lookup by the model's UUID column (used by API layer).

        Uses the uuid_column attribute to resolve the correct column.
        """
        col = getattr(self.model, self.uuid_column)
        result = await self.db.execute(select(self.model).where(col == uuid_str))
        return result.scalar_one_or_none()

    async def get_all(
        self, *, order_by=None, limit: int | None = None
    ) -> Sequence[ModelT]:
        """
        Fetch all rows with optional ordering and limit.

        Returns a sequence of model instances.
        """
        query = select(self.model)
        if order_by is not None:
            query = query.order_by(order_by)
        if limit is not None:
            query = query.limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create(self, entity: ModelT) -> ModelT:
        """Persist a new entity, flush, refresh, and return it."""
        self.db.add(entity)
        await self.db.flush()
        await self.db.refresh(entity)
        return entity

    async def update(self, entity: ModelT, data: dict) -> ModelT:
        """Update entity fields from dict, flush, refresh, and return."""
        for field, value in data.items():
            setattr(entity, field, value)
        await self.db.flush()
        await self.db.refresh(entity)
        return entity

    async def delete(self, entity: ModelT) -> None:
        """Delete the entity from the database."""
        await self.db.delete(entity)
