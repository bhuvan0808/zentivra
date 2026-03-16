"""
Zentivra Database Module.

Async SQLAlchemy engine and session factory for PostgreSQL (or SQLite for dev).
Handles SSL configuration for cloud databases (e.g. Railway, Aiven) and provides
a dependency-injectable session with automatic commit/rollback/close lifecycle.
"""

import ssl
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings, BASE_DIR

connect_args: dict = {}

# Only configure SSL for PostgreSQL connections (not SQLite)
if "postgresql" in settings.database_url:
    _cert_path_raw = settings.database_ca_cert_path
    if _cert_path_raw:
        _cert_path = Path(_cert_path_raw)
        if not _cert_path.is_absolute():
            _cert_path = BASE_DIR / _cert_path

        if _cert_path.exists():
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.load_verify_locations(str(_cert_path))
            # Enable hostname verification for security
            ctx.check_hostname = True
            ctx.verify_mode = ssl.CERT_REQUIRED
            connect_args["ssl"] = ctx
        else:
            # Cert file specified but missing — use generic require
            connect_args["ssl"] = "require"
    else:
        # No custom CA: use generic "require" so asyncpg negotiates TLS.
        # Railway, Aiven, Render all support this mode.
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
    """
    FastAPI dependency: yields a database session with automatic lifecycle.

    Session lifecycle: commit on success, rollback on exception, always close.
    Each request gets its own session; the session is scoped to the request.
    """
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


async def ensure_schema():
    """Add columns that may be missing from an older schema.

    Safe to call repeatedly — uses IF NOT EXISTS / checks before altering.
    """
    from sqlalchemy import text

    async with engine.begin() as conn:
        # Add meta JSONB column to findings if it doesn't exist
        await conn.execute(
            text(
                "ALTER TABLE findings ADD COLUMN IF NOT EXISTS meta JSONB DEFAULT NULL"
            )
        )


async def close_db():
    """Dispose of the database engine."""
    await engine.dispose()
