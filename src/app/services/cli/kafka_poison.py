from __future__ import annotations

import asyncio
from datetime import UTC, datetime
import re
from typing import Any

from aiokafka import AIOKafkaConsumer

from app.core.config import settings
from app.core.kafka import kafka_client

DEFAULT_REPLAY_LIMIT = 10
DEFAULT_IDLE_TIMEOUT_SECONDS = 2.0

POISON_HEADER_KEYS = {
    "poisoned_topic",
    "poisoned_handler",
    "poisoned_subscriber",
    "poisoned_reason",
    "poisoned-at",
    "poison-queue-topic",
}


def _sanitize_topic(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9-]+", "-", value.strip().lower())
    cleaned = re.sub(r"-+", "-", cleaned).strip("-")
    return cleaned or "app"


def _default_poison_topic() -> str:
    base = settings.KAFKA_CLIENT_ID or settings.APP_NAME
    return f"backend-{_sanitize_topic(base)}-poison-queue"


def _headers_to_dict(headers: list[tuple[str, bytes]] | None) -> dict[str, bytes]:
    if not headers:
        return {}
    return {key: value for key, value in headers}


def _filter_headers(headers: list[tuple[str, bytes]] | None, original_topic_header: str) -> list[tuple[str, bytes]]:
    if not headers:
        return []
    return [
        (key, value)
        for key, value in headers
        if key not in POISON_HEADER_KEYS and key != original_topic_header
    ]


async def replay_poison_messages(
    *,
    limit: int | None = None,
    poison_topic: str | None = None,
    original_topic_header: str = "poisoned_topic",
    original_topic: str | None = None,
    idle_timeout_seconds: float = DEFAULT_IDLE_TIMEOUT_SECONDS,
    group_id: str | None = None,
) -> dict[str, Any]:
    total_limit = limit if limit and limit > 0 else DEFAULT_REPLAY_LIMIT
    topic = poison_topic or _default_poison_topic()

    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=kafka_client._bootstrap_servers(),
        client_id=settings.KAFKA_CLIENT_ID,
        group_id=group_id or f"{settings.KAFKA_CONSUMER_GROUP}-poison-replay",
        enable_auto_commit=False,
        auto_offset_reset="earliest",
    )
    await consumer.start()

    processed = 0
    replayed = 0
    messages: list[dict[str, Any]] = []

    try:
        producer = await kafka_client.get_producer()
        while processed < total_limit:
            try:
                msg = await asyncio.wait_for(consumer.getone(), timeout=idle_timeout_seconds)
            except asyncio.TimeoutError:
                break

            processed += 1
            headers = _headers_to_dict(msg.headers)
            header_topic = headers.get(original_topic_header, b"").decode()
            target_topic = header_topic.strip() or (original_topic or "").strip()

            details: dict[str, Any] = {
                "poison_topic": topic,
                "original_topic": target_topic or None,
                "partition": msg.partition,
                "offset": msg.offset,
                "replayed": False,
            }

            if not target_topic:
                details["error"] = f"missing header {original_topic_header}"
                messages.append(details)
                break

            new_headers = _filter_headers(msg.headers, original_topic_header)
            new_headers.append(("poison-replayed-at", datetime.now(UTC).isoformat().encode()))

            await producer.send_and_wait(
                target_topic,
                msg.value,
                key=msg.key,
                headers=new_headers,
            )
            await consumer.commit()

            details["replayed"] = True
            replayed += 1
            messages.append(details)
    finally:
        await consumer.stop()

    if processed == 0:
        return {"poison_topic": topic, "processed": 0, "replayed": 0, "messages": [], "error": "no messages"}

    return {
        "poison_topic": topic,
        "processed": processed,
        "replayed": replayed,
        "messages": messages,
    }
