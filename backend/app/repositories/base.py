"""Base repository with generic async CRUD operations."""

from typing import Generic, Sequence, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Provides reusable get / create / update / delete for any SQLAlchemy model."""

    uuid_column: str = ""

    def __init__(self, model: type[ModelT], db: AsyncSession):
        self.model = model
        self.db = db

    async def get_by_id(self, entity_id: int) -> ModelT | None:
        """Lookup by integer PK (internal use only)."""
        result = await self.db.execute(
            select(self.model).where(self.model.id == entity_id)
        )
        return result.scalar_one_or_none()

    async def get_by_uuid(self, uuid_str: str) -> ModelT | None:
        """Lookup by the table's UUID column (used by API layer)."""
        col = getattr(self.model, self.uuid_column)
        result = await self.db.execute(
            select(self.model).where(col == uuid_str)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self, *, order_by=None, limit: int | None = None
    ) -> Sequence[ModelT]:
        query = select(self.model)
        if order_by is not None:
            query = query.order_by(order_by)
        if limit is not None:
            query = query.limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create(self, entity: ModelT) -> ModelT:
        self.db.add(entity)
        await self.db.flush()
        await self.db.refresh(entity)
        return entity

    async def update(self, entity: ModelT, data: dict) -> ModelT:
        for field, value in data.items():
            setattr(entity, field, value)
        await self.db.flush()
        await self.db.refresh(entity)
        return entity

    async def delete(self, entity: ModelT) -> None:
        await self.db.delete(entity)
