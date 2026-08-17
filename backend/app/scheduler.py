from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.database import async_session
from app.tle_fetcher import fetch_and_store_tles

scheduler = AsyncIOScheduler()


async def _refresh_job():
    async with async_session() as db:
        await fetch_and_store_tles(db)


def start_scheduler():
    scheduler.add_job(
        _refresh_job,
        "interval",
        minutes=settings.tle_refresh_minutes,
        id="tle_refresh",
        replace_existing=True,
    )
    scheduler.start()
