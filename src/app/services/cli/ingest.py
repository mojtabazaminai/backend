from __future__ import annotations

from datetime import datetime, timedelta, timezone
import re

from app.core.config import settings
from app.core.db.database import local_session
from app.services.ingest.crawll.foursquare_client import FoursquareClient
from app.services.ingest.crawll.foursquare_crawler import FoursquareCrawler
from app.services.ingest.service import IngestService

DEFAULT_CRAWL_WINDOW = timedelta(hours=24)


def parse_duration(value: str) -> timedelta:
    match = re.fullmatch(r"(\d+)([smhd])", value.strip())
    if not match:
        raise ValueError("since must be like 30m, 6h, 2d, 15s")
    amount = int(match.group(1))
    if amount <= 0:
        raise ValueError("since must be greater than zero")
    unit = match.group(2)
    if unit == "s":
        return timedelta(seconds=amount)
    if unit == "m":
        return timedelta(minutes=amount)
    if unit == "h":
        return timedelta(hours=amount)
    return timedelta(days=amount)


def crawl_since(window: timedelta) -> datetime:
    return datetime.now(timezone.utc) - window


async def run_crawl(window: timedelta) -> None:
    service = await IngestService.create()
    since = crawl_since(window)
    count = await service.crawl_mls_since(since)
    print(f"Crawled {count} properties since {since.isoformat()}")


async def run_crawl_csv() -> None:
    service = await IngestService.create()
    count = await service.crawl_mls_csv()
    print(f"Crawled {count} properties from CSV dumps")


async def run_crawl_foursquare() -> None:
    if not settings.FOURSQUARE_API_KEY:
        raise RuntimeError("FOURSQUARE_API_KEY is not configured.")
    client = FoursquareClient(settings.FOURSQUARE_API_KEY)
    async with local_session() as db:
        crawler = FoursquareCrawler(client, db)
        await crawler.crawl()
    await client.close()
    print("Foursquare crawl completed")


async def run_crawl_foursquare_debug(ne_lat: float, ne_lon: float, sw_lat: float, sw_lon: float) -> None:
    if not settings.FOURSQUARE_API_KEY:
        raise RuntimeError("FOURSQUARE_API_KEY is not configured.")
    client = FoursquareClient(settings.FOURSQUARE_API_KEY)
    async with local_session() as db:
        crawler = FoursquareCrawler(client, db)
        await crawler.debug_crawl(ne_lat=ne_lat, ne_lon=ne_lon, sw_lat=sw_lat, sw_lon=sw_lon)
    await client.close()
    print("Foursquare debug crawl completed")
