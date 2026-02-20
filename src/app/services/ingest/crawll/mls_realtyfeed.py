from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import logging

import httpx

from ....schemas.ingest import Channel, Pager, RawProperty

logger = logging.getLogger(__name__)


class RealtyFeedMLSClient:
    def __init__(self, base_url: str, client_id: str, client_secret: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self._auth: _AuthToken | None = None
        self._client = httpx.AsyncClient()

    async def _authenticate(self) -> None:
        if self._auth and self._auth.is_valid():
            return

        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        response = await self._client.post(
            f"{self.base_url}/v1/auth/token",
            data=payload,
            headers={"Accept": "*/*"},
        )
        response.raise_for_status()
        data = response.json()

        expires_in = int(data.get("expires_in", 0))
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        self._auth = _AuthToken(token=data.get("access_token", ""), expires_at=expires_at)

    async def get_properties_by_modified(self, pager: Pager, since: datetime) -> list[RawProperty]:
        await self._authenticate()

        if since.tzinfo is None:
            since = since.replace(tzinfo=timezone.utc)

        params = {
            "$top": str(pager.limit),
            "$skip": str(pager.offset()),
            "$select": "ALL",
            "$count": "true",
        }
        if since and since != datetime.min.replace(tzinfo=timezone.utc):
            skew = timedelta(minutes=1)
            stamp = (since - skew).astimezone(timezone.utc).isoformat()
            params["$filter"] = f"ModificationTimestamp ge '{stamp}'"
            params["$orderby"] = "ModificationTimestamp asc, ListingKey asc"

        headers = {
            "Authorization": f"Bearer {self._auth.token}",
            "Accept": "application/json",
        }
        response = await self._client.get(f"{self.base_url}/reso/odata/Property", params=params, headers=headers)
        response.raise_for_status()
        payload = response.json()

        if "@odata.count" in payload:
            try:
                pager.set_total(int(payload["@odata.count"]))
            except (TypeError, ValueError):
                logger.warning("Invalid @odata.count value: %s", payload.get("@odata.count"))

        properties: list[RawProperty] = []
        for item in payload.get("value", []):
            listing_id = item.get("ListingId", "") or ""
            listing_key = item.get("ListingKey", "") or ""
            standard_status = item.get("StandardStatus", "") or ""
            properties.append(
                RawProperty(
                    listing_key=listing_key,
                    listing_id=listing_id,
                    standard_status=standard_status,
                    channel=Channel.REALTYFEED,
                    data=item,
                )
            )
        return properties

    async def close(self) -> None:
        await self._client.aclose()


@dataclass
class _AuthToken:
    token: str
    expires_at: datetime

    def is_valid(self) -> bool:
        return bool(self.token) and self.expires_at > datetime.now(timezone.utc)
