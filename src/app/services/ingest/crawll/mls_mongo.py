from __future__ import annotations

from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase

from ....schemas.ingest import Channel, Pager, RawProperty


class MongoDBMLSClient:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db = db
        self.collection = self.db.get_collection("properties")

    async def get_properties_by_modified(self, pager: Pager, since: datetime) -> list[RawProperty]:
        if since.tzinfo is None:
            since = since.replace(tzinfo=timezone.utc)

        filter_query = {"modification_timestamp": {"$gte": since}}
        projection = {
            "_id": 1,
            "listing_id": 1,
            "standard_status": 1,
            "raw_api_data": 1,
            "modification_timestamp": 1,
            "crawled_at": 1,
        }

        cursor = self.collection.find(filter_query, projection=projection).sort("modification_timestamp", -1)

        if pager.limit > 0:
            cursor = cursor.limit(pager.limit)
        offset = pager.offset()
        if offset > 0:
            cursor = cursor.skip(offset)

        rows = await cursor.to_list(length=None)
        properties: list[RawProperty] = []
        for row in rows:
            listing_key = str(row.get("_id", ""))
            listing_id = row.get("listing_id", "") or ""
            standard_status = row.get("standard_status", "") or ""
            data = row.get("raw_api_data") or {}
            crawled_at = row.get("crawled_at")
            if crawled_at is not None and crawled_at.tzinfo is None:
                crawled_at = crawled_at.replace(tzinfo=timezone.utc)

            properties.append(
                RawProperty(
                    listing_key=listing_key,
                    listing_id=listing_id,
                    standard_status=standard_status,
                    channel=Channel.REALTYFEED,
                    data=data,
                    crawled_at=crawled_at,
                )
            )
        return properties
