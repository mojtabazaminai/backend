from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict


class Channel(str, Enum):
    UNKNOWN = ""
    REALTYFEED = "realtyfeed"


@dataclass
class Pager:
    page: int = 1
    limit: int = 20
    _total: int | None = None

    def __post_init__(self) -> None:
        if self.page < 1:
            self.page = 1
        if self.limit < 1:
            self.limit = 20
        if self.limit > 200:
            self.limit = 200

    @classmethod
    def default(cls) -> "Pager":
        return cls(page=1, limit=20)

    def offset(self) -> int:
        return (self.page - 1) * self.limit

    def set_total(self, total: int) -> None:
        self._total = max(total, 0)

    def is_last_page(self) -> bool:
        if self._total is None:
            return False
        total_pages = (self._total + self.limit - 1) // self.limit
        return self.page >= total_pages

    def advance_by(self, processed: int) -> None:
        if processed <= 0:
            return
        new_offset = self.offset() + processed
        self.page = (new_offset // self.limit) + 1


class RawProperty(BaseModel):
    listing_key: str
    listing_id: str
    standard_status: str
    channel: Channel
    data: Any
    crawled_at: datetime | None = None


class SocialMedia(BaseModel):
    facebook_id: str | None = None
    instagram: str | None = None
    twitter: str | None = None


@dataclass
class CategoryIcon:
    prefix: str
    suffix: str


@dataclass
class FoursquareCategory:
    id: str
    name: str
    icon: CategoryIcon


@dataclass
class FoursquareChain:
    id: str
    name: str


@dataclass
class Coordinates:
    latitude: float
    longitude: float


@dataclass
class Geocodes:
    main: Coordinates


@dataclass
class Location:
    address: str | None = None
    locality: str | None = None
    region: str | None = None
    postcode: str | None = None
    country: str | None = None


@dataclass
class FoursquareSocialMedia:
    facebook_id: str | None = None
    instagram: str | None = None
    twitter: str | None = None


@dataclass
class FoursquarePlace:
    fsq_place_id: str
    name: str
    categories: list[FoursquareCategory]
    chains: list[FoursquareChain]
    location: Location
    geocodes: Geocodes | None
    latitude: float | None
    longitude: float | None
    link: str | None
    rating: float | None
    price: int | None
    popularity: float | None
    social_media: FoursquareSocialMedia | None
    website: str | None


class CategoryBase(BaseModel):
    foursquare_id: str
    name: str
    icon_prefix: str | None = None
    icon_suffix: str | None = None


class CategoryCreate(CategoryBase):
    model_config = ConfigDict(extra="forbid")


class CategoryUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    foursquare_id: str | None = None
    name: str | None = None
    icon_prefix: str | None = None
    icon_suffix: str | None = None


class CategoryRead(CategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None


class ChainBase(BaseModel):
    foursquare_id: str
    name: str


class ChainCreate(ChainBase):
    model_config = ConfigDict(extra="forbid")


class ChainUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    foursquare_id: str | None = None
    name: str | None = None


class ChainRead(ChainBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None


class PointOfInterestBase(BaseModel):
    foursquare_id: str
    name: str
    latitude: float
    longitude: float
    address: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    popularity: float | None = None
    rating: float | None = None
    price: int | None = None
    website: str | None = None
    social_media: SocialMedia | None = None
    category_ids: list[int] | None = None
    chain_ids: list[int] | None = None


class PointOfInterestCreate(PointOfInterestBase):
    model_config = ConfigDict(extra="forbid")


class PointOfInterestUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    foursquare_id: str | None = None
    name: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    popularity: float | None = None
    rating: float | None = None
    price: int | None = None
    website: str | None = None
    social_media: SocialMedia | None = None
    category_ids: list[int] | None = None
    chain_ids: list[int] | None = None


class PointOfInterestRead(PointOfInterestBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None


class JobBase(BaseModel):
    source: str
    previous_id: int | None = None
    status: str


class JobCreate(JobBase):
    model_config = ConfigDict(extra="forbid")


class JobUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str | None = None
    previous_id: int | None = None
    status: str | None = None


class JobRead(JobBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None


class JobDelete(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_deleted: bool
    deleted_at: datetime
