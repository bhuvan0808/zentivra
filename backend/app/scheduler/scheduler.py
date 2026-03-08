"""
Scheduler - APScheduler-based job management for pipeline runs.

Key components:
- scheduled_run() - Entry point for scheduled triggers; creates RunTrigger
  and invokes Orchestrator.execute().
- sync_scheduler() - Syncs APScheduler jobs with DB Run configurations,
  builds _user_run_ids mapping for user-scoped status.
- start_scheduler() / stop_scheduler() - Lifecycle management.
- get_scheduler_status() - Returns job list, optionally filtered by user_id
  via _user_run_ids.

CronTrigger configuration:
- daily: runs at configured hour:minute (UTC) every day.
- weekly: runs on configured weekdays (e.g. mon,wed,fri) at configured time.
- monthly: runs on configured dates (e.g. 1,15) at configured time.
"""

import asyncio
from datetime import datetime, timezone

from app.utils.logger import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Global scheduler instance. None when scheduler is stopped.
_scheduler: AsyncIOScheduler | None = None

# Maps job_id (e.g. "run_123") -> frequency string ("daily"|"weekly"|"monthly").
# Used by get_scheduler_status() to include frequency in job details.
_job_frequencies: dict[str, str] = {}

# Maps user_id -> set of job_ids belonging to that user's runs.
# Enables user-scoped scheduler status: get_scheduler_status(user_id) returns
# only jobs for that user's runs.
_user_run_ids: dict[int, set[str]] = {}


async def scheduled_run(run_id: int):
    """
    Entry point for scheduled triggers.

    Creates a new RunTrigger (marks previous as non-latest), then invokes
    Orchestrator.execute() to run the full pipeline for the given run_id.
    """
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
    """
    Sync APScheduler jobs with DB Run configurations.

    Removes all existing jobs, rebuilds from enabled Runs. For each Run with
    crawl_frequency, adds a CronTrigger job. Updates _job_frequencies and
    _user_run_ids for status reporting.
    """
    global _scheduler, _job_frequencies, _user_run_ids
    if not _scheduler:
        return

    for job in _scheduler.get_jobs():
        job.remove()
    _job_frequencies.clear()
    _user_run_ids.clear()

    from app.database import async_session
    from app.models.run import Run
    from sqlalchemy import select

    async with async_session() as db:
        result = await db.execute(select(Run).where(Run.is_enabled == True))
        runs = result.scalars().all()

    jobs_added = 0
    for run in runs:
        cf = run.crawl_frequency
        if not cf:
            continue

        if isinstance(cf, str):
            parts = cf.split("|")
            freq = parts[0]
            time_str = parts[1] if len(parts) > 1 else "00:00"
            periods_raw = None
            if freq in ("weekly", "monthly") and len(parts) > 2:
                candidate = parts[2]
                if "/" not in candidate:
                    periods_raw = candidate.split(",")
            cf = {"frequency": freq, "time": time_str, "periods": periods_raw}

        if not isinstance(cf, dict):
            continue

        freq = cf.get("frequency")
        time_str = cf.get("time", "00:00")

        try:
            hour, minute = map(int, time_str.split(":"))
        except (ValueError, AttributeError):
            hour, minute = 0, 0

        periods = cf.get("periods")

        # CronTrigger: daily = every day at time; weekly = weekdays at time;
        # monthly = calendar dates at time.
        trigger = None
        if freq == "daily":
            trigger = CronTrigger(hour=hour, minute=minute, timezone="UTC")
        elif freq == "weekly":
            days = ",".join(periods) if periods else "mon"
            trigger = CronTrigger(
                day_of_week=days, hour=hour, minute=minute, timezone="UTC"
            )
        elif freq == "monthly":
            dates = ",".join(periods) if periods else "1"
            trigger = CronTrigger(day=dates, hour=hour, minute=minute, timezone="UTC")

        if trigger:
            job_id = f"run_{run.id}"
            _scheduler.add_job(
                scheduled_run,
                trigger=trigger,
                args=[run.id],
                id=job_id,
                name=f"Run {run.id}: {run.run_name}",
                replace_existing=True,
            )
            _job_frequencies[job_id] = freq
            _user_run_ids.setdefault(run.user_id, set()).add(job_id)
            jobs_added += 1

    logger.info("scheduler_synced total_jobs=%d", jobs_added)


async def start_scheduler():
    """Start the APScheduler instance and sync jobs from DB. Idempotent if already running."""
    global _scheduler

    if _scheduler is not None:
        logger.warning("scheduler_already_running")
        return

    _scheduler = AsyncIOScheduler()
    _scheduler.start()
    logger.info("scheduler_started")
    await sync_scheduler()


def stop_scheduler():
    """Stop the scheduler and clear the global instance."""
    global _scheduler
    if _scheduler:
        _scheduler.shutdown()
        _scheduler = None
        logger.info("scheduler_stopped")


def get_scheduler_status(user_id: int | None = None) -> dict:
    """
    Get current scheduler status (running flag + job list).

    When user_id is provided, returns only jobs for that user's runs via
    _user_run_ids. Otherwise returns all jobs.
    """
    if _scheduler is None:
        return {"running": False, "jobs": []}

    jobs = _scheduler.get_jobs()

    if user_id is not None:
        allowed = _user_run_ids.get(user_id, set())
        jobs = [j for j in jobs if j.id in allowed]

    return {
        "running": _scheduler.running,
        "jobs": [
            {
                "id": job.id,
                "name": job.name,
                "frequency": _job_frequencies.get(job.id),
                "next_run": str(job.next_run_time) if job.next_run_time else None,
            }
            for job in jobs
        ],
    }
