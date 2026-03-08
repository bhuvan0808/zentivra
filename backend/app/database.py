"""
Zentivra Database Module.

Async SQLAlchemy engine and session factory for PostgreSQL.
"""

import ssl
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings, BASE_DIR

connect_args: dict = {}
if settings.database_ca_cert_path:
    cert_path = Path(settings.database_ca_cert_path)
    if not cert_path.is_absolute():
        cert_path = BASE_DIR / cert_path
    ctx = ssl.create_default_context(cafile=str(cert_path))
    connect_args["ssl"] = ctx
else:
    connect_args["ssl"] = "require"

engine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,
    connect_args=connect_args,
    pool_size=5,
    max_overflow=10,
)

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
    """Create all tables (standalone utility, not called on startup)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Dispose of the database engine."""
    await engine.dispose()
