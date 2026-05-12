import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from .config import settings
from .sync import run_sync_cycle
import asyncio

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def sync_job():
    asyncio.run(run_sync_cycle())


if __name__ == "__main__":
    scheduler = BlockingScheduler()
    scheduler.add_job(
        sync_job,
        trigger=IntervalTrigger(hours=settings.sync_interval_hours),
        id="job_sync",
        next_run_time=None,  # run on first tick after startup delay
        replace_existing=True,
    )
    logger.info(
        "Job sync scheduler started — interval: %dh, country: %s",
        settings.sync_interval_hours,
        settings.target_country_code,
    )
    # Run once immediately at startup, then schedule
    sync_job()
    scheduler.start()
