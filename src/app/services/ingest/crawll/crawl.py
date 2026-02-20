from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from typing import Protocol

from aiokafka import AIOKafkaProducer

from ....schemas.ingest import Pager, RawProperty

logger = logging.getLogger(__name__)


class MLSClient(Protocol):
    async def get_properties_by_modified(self, pager: Pager, since: datetime) -> list[RawProperty]:
        ...


def _json_default(value):
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


class CrawlModule:
    def __init__(self, mls_client: MLSClient, producer: AIOKafkaProducer, raw_message_topic: str) -> None:
        self.mls_client = mls_client
        self.producer = producer
        self.raw_message_topic = raw_message_topic

    async def crawl(self, since: datetime) -> int:
        if since.tzinfo is None:
            since = since.replace(tzinfo=timezone.utc)

        pager = Pager.default()
        crawled_at = datetime.now(timezone.utc)
        count = 0

        while True:
            logger.info("ingest.crawl.page", extra={"page": pager.page, "crawled_at": crawled_at.isoformat()})
            properties = await self.mls_client.get_properties_by_modified(pager, since)
            if not properties:
                break

            batch = self.producer.create_batch()
            for prop in properties:
                payload = {
                    "listing_key": prop.listing_key,
                    "listing_id": prop.listing_id,
                    "status": prop.standard_status,
                    "channel": prop.channel.value,
                    "crawled_at": crawled_at,
                    "data": prop.data,
                }
                encoded = json.dumps(payload, default=_json_default).encode("utf-8")
                if batch is None or batch.append(value=encoded, key=None, timestamp=None) is None:
                    if batch is not None:
                        await self.producer.send_batch(batch, self.raw_message_topic)
                    batch = self.producer.create_batch()
                    if batch is None:
                        await self.producer.send_and_wait(self.raw_message_topic, encoded)
                    else:
                        batch.append(value=encoded, key=None, timestamp=None)

            if batch is not None and batch.record_count() > 0:
                await self.producer.send_batch(batch, self.raw_message_topic)

            count += len(properties)
            if pager.is_last_page():
                break
            pager.advance_by(len(properties))

        return count
