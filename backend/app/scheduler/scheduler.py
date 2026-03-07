"""
Scheduler - APScheduler-based pipeline scheduling per run configuration.
"""

import asyncio
from datetime import datetime, timezone

from app.utils.logger import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings

# Global scheduler instance
_scheduler: AsyncIOScheduler | None = None


async def scheduled_run(run_id: int):
    """Entry point for the scheduled daily run. Triggers specific run workflow."""
    from app.database import async_session
    from app.models.run_trigger import RunTrigger
    from app.scheduler.orchestrator import Orchestrator
    from sqlalchemy import update

    logger.info(
        "scheduled_run_triggered run_id=%s time=%s",
        run_id,
        datetime.now(timezone.utc).isoformat(),
    )

    async with async_session() as db:
        await db.execute(
            update(RunTrigger)
            .where((RunTrigger.run_id == run_id) & (RunTrigger.is_latest == True))
            .values(is_latest=False)
        )
        trigger = RunTrigger(
            run_id=run_id,
            trigger_method="scheduler",
            status="pending",
            is_latest=True,
        )
        db.add(trigger)
        await db.commit()
        await db.refresh(trigger)
        run_trigger_id = trigger.id

    orchestrator = Orchestrator()
    await orchestrator.execute(run_trigger_id=run_trigger_id, run_id=run_id, options={})


async def sync_scheduler():
    """Sync the APScheduler jobs with the Runs in the database."""
    global _scheduler
    if not _scheduler:
        return

    # Clear old jobs
    for job in _scheduler.get_jobs():
        job.remove()

    from app.database import async_session
    from app.models.run import Run
    from sqlalchemy import select

    async with async_session() as db:
        result = await db.execute(select(Run).where(Run.is_enabled == True))
        runs = result.scalars().all()

    jobs_added = 0
    for run in runs:
        if not run.crawl_frequency:
            continue

        parts = run.crawl_frequency.split("|")
        freq = parts[0]
        time_str = parts[1] if len(parts) > 1 else "00:00"

        try:
            hour, minute = map(int, time_str.split(":"))
        except ValueError:
            hour, minute = 0, 0

        tz = parts[-1] if len(parts) > 2 and "/" in parts[-1] else settings.timezone

        trigger = None
        if freq == "daily":
            trigger = CronTrigger(hour=hour, minute=minute, timezone=tz)
        elif freq == "weekly":
            days = parts[2] if len(parts) > 2 and parts[2] != tz else "mon"
            trigger = CronTrigger(
                day_of_week=days, hour=hour, minute=minute, timezone=tz
            )
        elif freq == "monthly":
            dates = parts[2] if len(parts) > 2 and parts[2] != tz else "1"
            trigger = CronTrigger(day=dates, hour=hour, minute=minute, timezone=tz)

        if trigger:
            _scheduler.add_job(
                scheduled_run,
                trigger=trigger,
                args=[run.id],
                id=f"run_{run.id}",
                name=f"Run {run.id}: {run.run_name}",
                replace_existing=True,
            )
            jobs_added += 1

    logger.info("scheduler_synced total_jobs=%d", jobs_added)


async def start_scheduler():
    """Start the APScheduler and sync jobs."""
    global _scheduler

    if _scheduler is not None:
        logger.warning("scheduler_already_running")
        return

    _scheduler = AsyncIOScheduler()
    _scheduler.start()
    logger.info("scheduler_started")
    await sync_scheduler()


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
