import os

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.database import async_session
from app.routers.digest import send_daily_digests
from app.services.feed_fetcher import poll_all_feeds

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


def _is_uvicorn_reloader_parent() -> bool:
    """Uvicorn --reload runs a parent watcher and a worker child; only the child should own jobs."""
    return os.environ.get("WATCHFILES_FORCE_COLORS") is not None and os.environ.get("RUN_MAIN") != "true"


async def _poll_job() -> None:
    logger.info("Starting scheduled feed poll")
    async with async_session() as db:
        result = await poll_all_feeds(db)
    logger.info("Feed poll complete, %s new articles", result["new_articles"])


async def _digest_job() -> None:
    sent = await send_daily_digests()
    if sent:
        logger.info("Sent %s digest notification(s)", sent)


def start_scheduler() -> None:
    if _is_uvicorn_reloader_parent():
        logger.info("Skipping scheduler in uvicorn reloader parent")
        return
    if scheduler.running:
        return
    scheduler.add_job(
        _poll_job,
        IntervalTrigger(minutes=settings.feed_poll_interval_minutes),
        id="feed_poll",
        replace_existing=True,
    )
    scheduler.add_job(
        _digest_job,
        CronTrigger(minute="*"),
        id="daily_digest",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started")


def shutdown_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
