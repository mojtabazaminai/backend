from __future__ import annotations

from app.core.config import settings
from app.core.search.elasticsearch import es_client


def _parse_indices(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


async def ensure_indices(indices: list[str] | str | None = None) -> dict[str, list[str]]:
    client = es_client.get_client()
    if isinstance(indices, str):
        indices = _parse_indices(indices)
    configured = indices or _parse_indices(settings.ELASTICSEARCH_INDEX)
    targets = configured or [settings.ELASTICSEARCH_INDEX]
    created: list[str] = []
    skipped: list[str] = []

    for index in targets:
        exists = await client.indices.exists(index=index)
        if exists:
            skipped.append(index)
            continue
        await client.indices.create(
            index=index,
            mappings={
                "properties": {
                    "latitude": {"type": "float"},
                    "longitude": {"type": "float"},
                    "location": {"type": "geo_point"},
                }
            },
        )
        created.append(index)

    return {"created": created, "skipped": skipped}
