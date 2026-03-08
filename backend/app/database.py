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

_cert_path_raw = settings.database_ca_cert_path
if _cert_path_raw:
    _cert_path = Path(_cert_path_raw)
    if not _cert_path.is_absolute():
        _cert_path = BASE_DIR / _cert_path

    if _cert_path.exists():
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.load_verify_locations(str(_cert_path))
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        connect_args["ssl"] = ctx
    else:
        connect_args["ssl"] = "require"
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
