"""
One-time table creation script for PostgreSQL.

Run once to create all tables:
    python -m scripts.init_db
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import engine, Base  # noqa: E402

import app.models.user  # noqa: E402, F401
import app.models.user_session  # noqa: E402, F401
import app.models.source  # noqa: E402, F401
import app.models.run  # noqa: E402, F401
import app.models.run_trigger  # noqa: E402, F401
import app.models.finding  # noqa: E402, F401
import app.models.snapshot  # noqa: E402, F401
import app.models.digest  # noqa: E402, F401
import app.models.digest_snapshot  # noqa: E402, F401
import app.models.orchestrator_config  # noqa: E402, F401


async def create_tables():
    print(f"Creating tables against: {engine.url}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("All tables created successfully.")


if __name__ == "__main__":
    asyncio.run(create_tables())
