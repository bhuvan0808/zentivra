"""
Zentivra Database Module.

Async SQLAlchemy engine and session factory.
Supports both SQLite (development) and PostgreSQL (production).
"""

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


# Create async engine
is_sqlite = "sqlite" in settings.database_url
engine = create_async_engine(
    settings.database_url,
    echo=(settings.app_env.value == "development"),
    # For SQLite, we need check_same_thread=False
    connect_args=(
        {"check_same_thread": False, "timeout": 60}
        if is_sqlite
        else {}
    ),
)

if is_sqlite:
    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, connection_record):  # type: ignore[no-redef]
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA busy_timeout=60000;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.close()

# Session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


async def get_db() -> AsyncSession:
    """FastAPI dependency: yields a database session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Create all tables. Used in development with SQLite."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# TODO: Remove this seeding logic before production deployment
async def seed_sources_if_empty():
    """Insert default sources from backup JSON when the table is empty."""
    import json
    import os

    from sqlalchemy import func, select

    from app.models.source import Source

    backup_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sources_backup.json")
    if not os.path.exists(backup_path):
        return

    async with async_session() as session:
        count = await session.scalar(select(func.count()).select_from(Source))
        if count and count > 0:
            return

        with open(backup_path, "r", encoding="utf-8") as f:
            records = json.load(f)

        for rec in records:
            source = Source(
                source_id=rec["id"],
                source_name=rec["name"].lower().replace(" ", "_"),
                display_name=rec["name"],
                agent_type=rec["agent_type"].lower(),
                url=rec["url"],
                is_enabled=bool(rec.get("enabled", 1)),
            )
            session.add(source)

        await session.commit()
# END TODO


async def close_db():
    """Dispose of the database engine."""
    await engine.dispose()
