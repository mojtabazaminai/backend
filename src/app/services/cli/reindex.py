from __future__ import annotations

from typing import Any

from sqlalchemy import select

from app.core.config import settings
from app.core.db.database import local_session
from app.core.search.elasticsearch import es_client
from app.models.property import Property

DEFAULT_BATCH_SIZE = 500
MAX_BATCH_SIZE = 5000


def clamp_batch_size(value: int | None) -> int:
    if not value or value <= 0:
        return DEFAULT_BATCH_SIZE
    if value > MAX_BATCH_SIZE:
        return MAX_BATCH_SIZE
    return value


def _normalize(value: str | None, *, upper: bool = False) -> str:
    if not value:
        return ""
    cleaned = value.strip()
    return cleaned.upper() if upper else cleaned.lower()


def _build_document(prop: Property) -> dict[str, Any]:
    doc: dict[str, Any] = {
        "listing_key": prop.listing_key,
        "standard_status": _normalize(prop.standard_status),
        "property_type": _normalize(prop.property_type),
        "list_price": prop.list_price,
        "unparsed_address": (prop.unparsed_address or "").strip(),
        "city": _normalize(prop.city),
        "state_or_province": _normalize(prop.state_or_province),
        "postal_code": _normalize(prop.postal_code),
        "primary_photo": prop.primary_photo,
        "bedrooms_total": prop.bedrooms_total,
        "bathrooms_total_integer": prop.bathrooms_total_integer,
        "created_at": prop.created_at.isoformat() if prop.created_at else None,
        "updated_at": prop.updated_at.isoformat() if prop.updated_at else None,
        "latitude": prop.latitude,
        "longitude": prop.longitude,
    }
    if prop.latitude is not None and prop.longitude is not None:
        doc["location"] = {"lat": prop.latitude, "lon": prop.longitude}
    return doc


def _count_bulk_successes(items: list[dict[str, Any]]) -> int:
    successes = 0
    for item in items:
        result = item.get("index") or {}
        status = result.get("status")
        if status is not None and int(status) < 300:
            successes += 1
    return successes


async def reindex_properties(start_after: str | None = None, batch_size: int | None = None) -> dict[str, Any]:
    index_name = settings.ELASTICSEARCH_INDEX
    size = clamp_batch_size(batch_size)
    last_key = (start_after or "").strip()
    total_indexed = 0
    processed_batches = 0

    client = es_client.get_client()

    async with local_session() as db:
        while True:
            query = select(Property).order_by(Property.listing_key).limit(size)
            if last_key:
                query = query.where(Property.listing_key > last_key)

            result = await db.execute(query)
            batch = result.scalars().all()
            if not batch:
                break

            operations: list[dict[str, Any]] = []
            for prop in batch:
                if not prop.listing_key:
                    continue
                operations.append({"index": {"_id": prop.listing_key}})
                operations.append(_build_document(prop))

            if not operations:
                last_key = batch[-1].listing_key
                processed_batches += 1
                continue

            response = await client.bulk(index=index_name, operations=operations)
            items = response.get("items", [])
            total_indexed += _count_bulk_successes(items)
            last_key = batch[-1].listing_key
            processed_batches += 1

    return {
        "indexed": total_indexed,
        "last_listing_key": last_key,
        "completed": True,
        "processed_batches": processed_batches,
    }
