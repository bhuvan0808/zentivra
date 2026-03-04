"""
Scheduler - APScheduler-based daily pipeline scheduling.

Configures a cron trigger to run the pipeline daily at the configured time.
Also exposes functions for manual triggering.
"""

import asyncio
from datetime import datetime, timezone

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings

logger = structlog.get_logger(__name__)

# Global scheduler instance
_scheduler: AsyncIOScheduler | None = None


async def scheduled_run():
    """
    Entry point for the scheduled daily run.

    Creates a new Run record and passes it to the Orchestrator.
    """
    from app.database import async_session
    from app.models.run import Run
    from app.scheduler.orchestrator import Orchestrator

    logger.info("scheduled_run_triggered", time=datetime.now(timezone.utc).isoformat())

    async with async_session() as db:
        run = Run(triggered_by="scheduler")
        db.add(run)
        await db.commit()
        await db.refresh(run)
        run_id = run.id

    orchestrator = Orchestrator()
    await orchestrator.execute_run(run_id)


async def manual_trigger() -> str:
    """
    Trigger a pipeline run manually.

    Returns the run_id.
    """
    from app.database import async_session
    from app.models.run import Run
    from app.scheduler.orchestrator import Orchestrator

    logger.info("manual_run_triggered")

    async with async_session() as db:
        run = Run(triggered_by="manual")
        db.add(run)
        await db.commit()
        await db.refresh(run)
        run_id = run.id

    # Run in background
    asyncio.create_task(
        _execute_in_background(run_id)
    )

    return run_id


async def _execute_in_background(run_id: str):
    """Execute the pipeline in a background task."""
    try:
        orchestrator = Orchestrator()
        await orchestrator.execute_run(run_id)
    except Exception as e:
        logger.error("background_run_error", run_id=run_id[:8], error=str(e))

        # Update run status to failed
        from app.database import async_session
        from app.models.run import Run, RunStatus
        from sqlalchemy import select

        async with async_session() as db:
            result = await db.execute(select(Run).where(Run.id == run_id))
            run = result.scalar_one_or_none()
            if run:
                run.status = RunStatus.FAILED
                run.error_log = str(e)
                run.completed_at = datetime.now(timezone.utc)
                await db.commit()


def start_scheduler():
    """
    Start the APScheduler with a daily cron trigger.

    Reads schedule time from settings.
    """
    global _scheduler

    if _scheduler is not None:
        logger.warning("scheduler_already_running")
        return

    _scheduler = AsyncIOScheduler()

    # Parse digest time (HH:MM format)
    try:
        hour, minute = settings.digest_time.split(":")
        hour = int(hour)
        minute = int(minute)
    except (ValueError, AttributeError):
        hour, minute = 6, 0

    # Add daily job
    _scheduler.add_job(
        scheduled_run,
        trigger=CronTrigger(
            hour=hour,
            minute=minute,
            timezone=settings.timezone,
        ),
        id="daily_digest",
        name="Daily AI Radar Digest",
        replace_existing=True,
    )

    _scheduler.start()
    logger.info(
        "scheduler_started",
        digest_time=f"{hour:02d}:{minute:02d}",
        timezone=settings.timezone,
    )


def stop_scheduler():
    """Stop the scheduler."""
    global _scheduler
    if _scheduler:
        _scheduler.shutdown()
        _scheduler = None
        logger.info("scheduler_stopped")


def get_scheduler_status() -> dict:
    """Get the current scheduler status."""
    if _scheduler is None:
        return {"running": False}

    jobs = _scheduler.get_jobs()
    return {
        "running": _scheduler.running,
        "jobs": [
            {
                "id": job.id,
                "name": job.name,
                "next_run": str(job.next_run_time) if job.next_run_time else None,
            }
            for job in jobs
        ],
    }
