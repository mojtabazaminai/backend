from __future__ import annotations

import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ....crud.crud_ingest_category import crud_ingest_category
from ....crud.crud_ingest_chain import crud_ingest_chain
from ....crud.crud_ingest_pointofinterest import crud_ingest_pointofinterest
from ....schemas.ingest import (
    CategoryCreate,
    ChainCreate,
    FoursquareCategory,
    FoursquareChain,
    FoursquarePlace,
    PointOfInterestCreate,
    PointOfInterestUpdate,
)
from .foursquare_client import FoursquareClient
from .grid import BBox, generate_grid

logger = logging.getLogger(__name__)

SD_NORTH = 33.11
SD_SOUTH = 32.53
SD_EAST = -116.90
SD_WEST = -117.26

SEARCH_LIMIT = 50

RELEVANT_CATEGORIES = [
    "4bf58dd8d48988d1e0931735",  # Coffee Shop
    "4d4b7105d754a06374d81259",  # Restaurant
    "4bf58dd8d48988d1fd941735",  # Shopping Mall
    "4bf58dd8d48988d163941735",  # Park
    "4bf58dd8d48988d13b941735",  # School
    "4bf58dd8d48988d118951735",  # Grocery Store
]


class FoursquareCrawler:
    def __init__(self, client: FoursquareClient, db: AsyncSession) -> None:
        self.client = client
        self.db = db
        self._category_cache: dict[str, int] = {}
        self._chain_cache: dict[str, int] = {}

    async def crawl(self) -> None:
        bbox = BBox(north=SD_NORTH, south=SD_SOUTH, east=SD_EAST, west=SD_WEST)
        await self.crawl_grid(bbox)

    async def debug_crawl(self, ne_lat: float, ne_lon: float, sw_lat: float, sw_lon: float) -> None:
        bbox = BBox(north=ne_lat, south=sw_lat, east=ne_lon, west=sw_lon)
        await self.crawl_grid(bbox)

    async def crawl_grid(self, target_bbox: BBox) -> None:
        tiles = generate_grid(target_bbox)
        if tiles:
            snapped_bbox = BBox(
                south=tiles[0].south,
                west=tiles[0].west,
                north=tiles[-1].north,
                east=tiles[-1].east,
            )
            logger.info("foursquare.grid", extra={"tiles": len(tiles), "snapped_bbox": snapped_bbox})

        for idx, tile in enumerate(tiles):
            try:
                await self._process_tile(tile)
            except Exception as exc:  # noqa: BLE001
                logger.warning("foursquare.tile.failed", extra={"index": idx, "error": str(exc)})

    async def _process_tile(self, bbox: BBox) -> None:
        cursor = ""
        while True:
            results, next_cursor = await self.client.search_places(
                RELEVANT_CATEGORIES,
                ne_lat=bbox.north,
                ne_lon=bbox.east,
                sw_lat=bbox.south,
                sw_lon=bbox.west,
                limit=SEARCH_LIMIT,
                cursor=cursor or None,
            )

            for place in results:
                await self._upsert_place(place)

            if not next_cursor:
                break
            cursor = next_cursor

    async def _resolve_category_ids(self, categories: list[FoursquareCategory]) -> list[int]:
        ids: list[int] = []
        for cat in categories:
            cached = self._category_cache.get(cat.id)
            if cached is not None:
                ids.append(cached)
                continue

            existing = await crud_ingest_category.get(db=self.db, foursquare_id=cat.id, return_as_model=True)
            if existing is None:
                create_in = CategoryCreate(
                    foursquare_id=cat.id,
                    name=cat.name,
                    icon_prefix=cat.icon.prefix if cat.icon else None,
                    icon_suffix=cat.icon.suffix if cat.icon else None,
                )
                try:
                    existing = await crud_ingest_category.create(db=self.db, object=create_in, return_as_model=True)
                except IntegrityError:
                    await self.db.rollback()
                    existing = await crud_ingest_category.get(
                        db=self.db, foursquare_id=cat.id, return_as_model=True
                    )

            if existing is None:
                continue

            self._category_cache[cat.id] = existing.id
            ids.append(existing.id)
        return ids

    async def _resolve_chain_ids(self, chains: list[FoursquareChain]) -> list[int]:
        ids: list[int] = []
        for chain in chains:
            cached = self._chain_cache.get(chain.id)
            if cached is not None:
                ids.append(cached)
                continue

            existing = await crud_ingest_chain.get(db=self.db, foursquare_id=chain.id, return_as_model=True)
            if existing is None:
                create_in = ChainCreate(foursquare_id=chain.id, name=chain.name)
                try:
                    existing = await crud_ingest_chain.create(db=self.db, object=create_in, return_as_model=True)
                except IntegrityError:
                    await self.db.rollback()
                    existing = await crud_ingest_chain.get(
                        db=self.db, foursquare_id=chain.id, return_as_model=True
                    )

            if existing is None:
                continue

            self._chain_cache[chain.id] = existing.id
            ids.append(existing.id)
        return ids

    async def _upsert_place(self, place: FoursquarePlace) -> None:
        category_ids = await self._resolve_category_ids(place.categories)
        chain_ids = await self._resolve_chain_ids(place.chains)

        lat = place.latitude or (place.geocodes.main.latitude if place.geocodes else 0.0)
        lon = place.longitude or (place.geocodes.main.longitude if place.geocodes else 0.0)

        social_media = None
        if place.social_media:
            social_media = {
                "facebook_id": place.social_media.facebook_id,
                "instagram": place.social_media.instagram,
                "twitter": place.social_media.twitter,
            }

        payload = {
            "foursquare_id": place.fsq_place_id,
            "name": place.name,
            "latitude": lat,
            "longitude": lon,
            "address": place.location.address or "",
            "city": place.location.locality or "",
            "state": place.location.region or "",
            "zip_code": place.location.postcode or "",
            "popularity": place.popularity,
            "rating": place.rating,
            "price": place.price,
            "website": place.website,
            "social_media": social_media,
            "category_ids": category_ids,
            "chain_ids": chain_ids,
        }

        existing = await crud_ingest_pointofinterest.get(
            db=self.db, foursquare_id=place.fsq_place_id, return_as_model=True
        )
        if existing is None:
            create_in = PointOfInterestCreate(**payload)
            await crud_ingest_pointofinterest.create(db=self.db, object=create_in)
            return

        update_in = PointOfInterestUpdate(**payload)
        await crud_ingest_pointofinterest.update(db=self.db, id=existing.id, object=update_in)
