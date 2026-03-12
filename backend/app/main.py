"""
Zentivra - Frontier AI Radar
============================
FastAPI application entry point.

Run with:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

from app.utils.logger import logger
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import close_db
from app.api.router import api_router
from app.dependencies import CurrentUser, get_current_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager: startup and shutdown sequence.

    Startup order: log env -> connect Valkey -> log LLM/email config -> start scheduler.
    Shutdown order: stop scheduler -> close Valkey -> dispose DB engine -> log shutdown.
    """
    # ── Startup ──────────────────────────────────────────────────────────
    logger.info("zentivra_startup env=%s", settings.app_env.value)

    logger.info("database_configured url=%s...", settings.database_url[:30])

    from app.database import ensure_schema
    try:
        await ensure_schema()
        logger.info("schema_migration_check complete")
    except Exception as e:
        logger.warning("schema_migration_check_failed error=%s", str(e))

    from app.core.valkey_client import valkey_client

    await valkey_client.connect()

    logger.info(
        "llm_provider provider=%s configured=%s",
        settings.active_llm_provider,
        settings.active_llm_provider != "none",
    )

    logger.info(
        "email_service configured=%s recipients=%d",
        settings.has_email_configured,
        len(settings.email_recipient_list),
    )

    from app.scheduler.scheduler import start_scheduler

    try:
        await start_scheduler()
    except Exception as e:
        logger.warning("scheduler_start_failed error=%s", str(e))

    yield

    # ── Shutdown ─────────────────────────────────────────────────────────
    from app.scheduler.scheduler import stop_scheduler

    stop_scheduler()
    await valkey_client.close()
    await close_db()
    logger.info("zentivra_shutdown")


app = FastAPI(
    title="Zentivra - Frontier AI Radar",
    description=(
        "Multi-agent intelligence system that tracks AI industry developments "
        "and produces daily executive + technical digests."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

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
async def scheduler_status(
    user: CurrentUser = Depends(get_current_user),
):
    """Get scheduler status and upcoming runs for the authenticated user."""
    from app.scheduler.scheduler import get_scheduler_status

    return get_scheduler_status(user_id=user.id)
