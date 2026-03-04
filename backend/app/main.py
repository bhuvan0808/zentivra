"""
Zentivra - Frontier AI Radar
============================
FastAPI application entry point.

Run with:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

import structlog
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db, close_db
from app.api.router import api_router


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    # ── Startup ──────────────────────────────────────────────────────────
    logger.info("zentivra_startup", env=settings.app_env.value)

    # Initialize database tables (creates them if using SQLite)
    await init_db()
    logger.info("database_initialized", url=settings.database_url[:30] + "...")

    # Seed default sources from YAML config (if DB is empty)
    await _seed_sources_from_config()

    # Log LLM provider status
    logger.info(
        "llm_provider",
        provider=settings.active_llm_provider,
        configured=settings.active_llm_provider != "none",
    )

    # Log email status
    logger.info(
        "email_service",
        configured=settings.has_email_configured,
        recipients=len(settings.email_recipient_list),
    )

    # Start the daily scheduler
    from app.scheduler.scheduler import start_scheduler
    try:
        start_scheduler()
        logger.info("scheduler_started")
    except Exception as e:
        logger.warning("scheduler_start_failed", error=str(e))

    yield

    # ── Shutdown ─────────────────────────────────────────────────────────
    from app.scheduler.scheduler import stop_scheduler
    stop_scheduler()
    await close_db()
    logger.info("zentivra_shutdown")


# Create FastAPI app
app = FastAPI(
    title="Zentivra - Frontier AI Radar",
    description=(
        "Multi-agent intelligence system that tracks AI industry developments "
        "and produces daily executive + technical digests."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware (allow frontend to connect)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "name": "Zentivra - Frontier AI Radar",
        "version": "1.0.0",
        "status": "operational",
        "llm_provider": settings.active_llm_provider,
        "email_configured": settings.has_email_configured,
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "database": "connected",
        "llm_provider": settings.active_llm_provider,
        "email_configured": settings.has_email_configured,
        "environment": settings.app_env.value,
    }


@app.get("/scheduler", tags=["Health"])
async def scheduler_status():
    """Get scheduler status and next run time."""
    from app.scheduler.scheduler import get_scheduler_status
    return get_scheduler_status()


async def _seed_sources_from_config():
    """
    Seed the database with sources from agents.yaml if the sources table is empty.
    This only runs on first startup or fresh DB.
    """
    import yaml
    from pathlib import Path
    from sqlalchemy import select, func
    from app.database import async_session
    from app.models.source import Source, AgentType

    config_path = Path(__file__).parent.parent / "config" / "agents.yaml"
    if not config_path.exists():
        logger.warning("agents_config_not_found", path=str(config_path))
        return

    async with async_session() as session:
        # Check if sources already exist
        result = await session.execute(select(func.count(Source.id)))
        count = result.scalar() or 0
        if count > 0:
            logger.info("sources_already_seeded", count=count)
            return

        # Load YAML config
        with open(config_path) as f:
            config = yaml.safe_load(f)

        agent_type_map = {
            "competitors": AgentType.COMPETITOR,
            "model_providers": AgentType.MODEL_PROVIDER,
            "research": AgentType.RESEARCH,
            "hf_benchmarks": AgentType.HF_BENCHMARK,
        }

        total_seeded = 0
        for section, agent_type in agent_type_map.items():
            sources = config.get(section, [])
            for src in sources:
                source = Source(
                    agent_type=agent_type,
                    name=src["name"],
                    url=src["url"],
                    feed_url=src.get("feed_url"),
                    css_selectors=src.get("css_selectors"),
                    keywords=src.get("keywords"),
                    rate_limit_rpm=src.get("rate_limit_rpm", 10),
                )
                session.add(source)
                total_seeded += 1

        await session.commit()
        logger.info("sources_seeded_from_config", total=total_seeded)
