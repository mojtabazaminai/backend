from __future__ import annotations

from datetime import datetime, timezone
import logging

from aiokafka import AIOKafkaProducer
from motor.motor_asyncio import AsyncIOMotorDatabase

from ...core.config import settings
from ...core.kafka import kafka_client
from ...core.mongodb import mongo_client
from ...schemas.ingest import Pager
from .crawll.crawl import CrawlModule, MLSClient
from .crawll.mls_csv import CSVMLSClient
from .crawll.mls_mongo import MongoDBMLSClient
from .crawll.mls_realtyfeed import RealtyFeedMLSClient

logger = logging.getLogger(__name__)

class IngestService:
    def __init__(self, mongo: AsyncIOMotorDatabase, producer: AIOKafkaProducer) -> None:
        self.mongo = mongo
        self.producer = producer
        self.mls_client = self._build_mls_client()
        self.crawler = CrawlModule(
            mls_client=self.mls_client,
            producer=self.producer,
            raw_message_topic=settings.MLS_RAW_MESSAGE_TOPIC,
        )

    @classmethod
    async def create(cls) -> "IngestService":
        mongo = mongo_client.get_database()
        producer = await kafka_client.get_producer()
        return cls(mongo=mongo, producer=producer)

    def _build_mls_client(self) -> MLSClient:
        source = settings.MLS_SOURCE.lower().strip()
        if source == "mongodb":
            return MongoDBMLSClient(self.mongo)
        if source in {"realty_feed", "realtyfeed"}:
            return RealtyFeedMLSClient(
                base_url=settings.MLS_REALTYFEED_URL,
                client_id=settings.MLS_REALTYFEED_CLIENT_ID,
                client_secret=settings.MLS_REALTYFEED_CLIENT_SECRET,
            )
        if source == "local_file":
            return CSVMLSClient(settings.MLS_STORAGE_LOCAL_DIRECTORY)

        logger.warning("Unknown MLS_SOURCE=%s; defaulting to local_file", source)
        return CSVMLSClient(settings.MLS_STORAGE_LOCAL_DIRECTORY)

    async def crawl_mls(self, since: datetime | None = None) -> int:
        since = since or datetime.min.replace(tzinfo=timezone.utc)
        return await self.crawler.crawl(since)

    async def crawl_mls_csv(self) -> int:
        if not isinstance(self.mls_client, CSVMLSClient):
            self.mls_client = CSVMLSClient(settings.MLS_STORAGE_LOCAL_DIRECTORY)
            self.crawler.mls_client = self.mls_client
        return await self.crawler.crawl(datetime.min.replace(tzinfo=timezone.utc))

    async def crawl_mls_since(self, since: datetime) -> int:
        return await self.crawler.crawl(since)

    async def list_mls_page(self, pager: Pager, since: datetime | None = None):
        since = since or datetime.min.replace(tzinfo=timezone.utc)
        return await self.mls_client.get_properties_by_modified(pager, since)
