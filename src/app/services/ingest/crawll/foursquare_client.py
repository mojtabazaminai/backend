from __future__ import annotations

import logging
from typing import Any
from urllib.parse import parse_qs, urlparse

import httpx

from ....schemas.ingest import (
    CategoryIcon,
    Coordinates,
    FoursquareCategory,
    FoursquareChain,
    FoursquarePlace,
    FoursquareSocialMedia,
    Geocodes,
    Location,
)

logger = logging.getLogger(__name__)

BASE_URL = "https://places-api.foursquare.com"
API_VERSION = "2025-06-17"


class FoursquareClient:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self._client = httpx.AsyncClient()

    async def search_places(
        self,
        categories: list[str],
        ne_lat: float,
        ne_lon: float,
        sw_lat: float,
        sw_lon: float,
        limit: int = 50,
        cursor: str | None = None,
    ) -> tuple[list[FoursquarePlace], str]:
        params = {
            "ne": f"{ne_lat},{ne_lon}",
            "sw": f"{sw_lat},{sw_lon}",
            "limit": str(limit),
            "fields": ",".join(
                [
                    "fsq_place_id",
                    "name",
                    "categories",
                    "chains",
                    "location",
                    "link",
                    "rating",
                    "price",
                    "popularity",
                    "social_media",
                    "website",
                    "latitude",
                    "longitude",
                    "geocodes",
                ]
            ),
        }
        if categories:
            params["categories"] = ",".join(categories)
        if cursor:
            params["cursor"] = cursor

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-Places-Api-Version": API_VERSION,
            "Accept": "application/json",
        }
        response = await self._client.get(f"{BASE_URL}/places/search", params=params, headers=headers)
        response.raise_for_status()
        payload = response.json()

        places = [self._parse_place(item) for item in payload.get("results", [])]
        next_cursor = self._parse_next_cursor(response.headers.get("Link"))
        return places, next_cursor

    def _parse_place(self, data: dict[str, Any]) -> FoursquarePlace:
        categories = [self._parse_category(cat) for cat in data.get("categories", [])]
        chains = [self._parse_chain(chain) for chain in data.get("chains", [])]
        location = self._parse_location(data.get("location", {}) or {})
        geocodes = self._parse_geocodes(data.get("geocodes"))
        social_media = self._parse_social_media(data.get("social_media"))

        return FoursquarePlace(
            fsq_place_id=data.get("fsq_place_id", ""),
            name=data.get("name", ""),
            categories=categories,
            chains=chains,
            location=location,
            geocodes=geocodes,
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            link=data.get("link"),
            rating=data.get("rating"),
            price=data.get("price"),
            popularity=data.get("popularity"),
            social_media=social_media,
            website=data.get("website"),
        )

    @staticmethod
    def _parse_category(data: dict[str, Any]) -> FoursquareCategory:
        icon_data = data.get("icon") or {}
        icon = CategoryIcon(prefix=icon_data.get("prefix", ""), suffix=icon_data.get("suffix", ""))
        return FoursquareCategory(id=str(data.get("id", "")), name=data.get("name", ""), icon=icon)

    @staticmethod
    def _parse_chain(data: dict[str, Any]) -> FoursquareChain:
        return FoursquareChain(id=str(data.get("id", "")), name=data.get("name", ""))

    @staticmethod
    def _parse_location(data: dict[str, Any]) -> Location:
        return Location(
            address=data.get("address"),
            locality=data.get("locality"),
            region=data.get("region"),
            postcode=data.get("postcode"),
            country=data.get("country"),
        )

    @staticmethod
    def _parse_geocodes(data: dict[str, Any] | None) -> Geocodes | None:
        if not data or "main" not in data:
            return None
        main = data.get("main") or {}
        return Geocodes(main=Coordinates(latitude=main.get("latitude", 0.0), longitude=main.get("longitude", 0.0)))

    @staticmethod
    def _parse_social_media(data: dict[str, Any] | None) -> FoursquareSocialMedia | None:
        if not data:
            return None
        return FoursquareSocialMedia(
            facebook_id=data.get("facebook_id"),
            instagram=data.get("instagram"),
            twitter=data.get("twitter"),
        )

    @staticmethod
    def _parse_next_cursor(link_header: str | None) -> str:
        if not link_header:
            return ""
        parts = link_header.split(";")
        if not parts:
            return ""
        url_part = parts[0].strip().strip("<>").strip()
        parsed = urlparse(url_part)
        cursor = parse_qs(parsed.query).get("cursor")
        return cursor[0] if cursor else ""

    async def close(self) -> None:
        await self._client.aclose()
