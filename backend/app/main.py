"""
Zentivra - Frontier AI Radar
============================
FastAPI application entry point.

Run with:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

import time

from app.utils.logger import logger
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import init_db, close_db, seed_sources_if_empty
from app.api.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    # ── Startup ──────────────────────────────────────────────────────────
    logger.info("zentivra_startup env=%s", settings.app_env.value)

    # Initialize database tables (creates them if using SQLite)
    await init_db()
    logger.info("database_initialized url=%s...", settings.database_url[:30])

    # TODO: Remove seed call before production deployment
    await seed_sources_if_empty()
    # END TODO

    # Connect to Redis for session caching (graceful fallback if unavailable)
    from app.core.redis_client import redis_client

    await redis_client.connect()

    # Log LLM provider status
    logger.info(
        "llm_provider provider=%s configured=%s",
        settings.active_llm_provider,
        settings.active_llm_provider != "none",
    )

    # Log email status
    logger.info(
        "email_service configured=%s recipients=%d",
        settings.has_email_configured,
        len(settings.email_recipient_list),
    )

    # Start the daily scheduler
    from app.scheduler.scheduler import start_scheduler

    try:
        start_scheduler()
        logger.info("scheduler_started")
    except Exception as e:
        logger.warning("scheduler_start_failed error=%s", str(e))

    yield

    # ── Shutdown ─────────────────────────────────────────────────────────
    from app.scheduler.scheduler import stop_scheduler

    stop_scheduler()
    await redis_client.close()
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
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Include API routes
app.include_router(api_router)


# ── Global Exception Handlers ────────────────────────────────────────────


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return 422 validation errors in a consistent shape."""
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all for unhandled errors so the client always gets JSON."""
    logger.error("unhandled_error path=%s error=%s", request.url.path, str(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


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
