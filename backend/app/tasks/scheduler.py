"""APScheduler — relance périodiquement les pipelines de scraping."""
from __future__ import annotations

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import get_settings
from app.database import SessionLocal
from app.services import ingest, elo

logger = logging.getLogger(__name__)
_scheduler: AsyncIOScheduler | None = None


async def _job_rankings():
    db = SessionLocal()
    try:
        await ingest.run_rankings_pipeline(db)
    finally:
        db.close()


async def _job_matches_and_elo():
    db = SessionLocal()
    try:
        await ingest.ingest_all_players_matches(db, top_n=200, concurrency=1)
        elo.recompute_elo(db)
    finally:
        db.close()


def start_scheduler() -> AsyncIOScheduler | None:
    global _scheduler
    s = get_settings()
    if not s.enable_scheduler:
        return None
    if _scheduler is not None:
        return _scheduler
    sched = AsyncIOScheduler(timezone="UTC")
    sched.add_job(_job_rankings, CronTrigger.from_crontab(s.rankings_cron), id="rankings")
    sched.add_job(_job_matches_and_elo, CronTrigger.from_crontab(s.matches_cron), id="matches")
    sched.start()
    _scheduler = sched
    logger.info("Scheduler started (rankings=%s, matches=%s)", s.rankings_cron, s.matches_cron)
    return sched


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
