from typing import Annotated, Any, Dict, Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.db.database import async_get_db
from ...crud import crud_property
from ...models.property import PropertyMedia as PropertyMediaModel
from ...schemas.property import (
    PropertyDetailResponse,
    PropertyListResponse,
    PropertyMediaItem,
    PropertySuggestResponse,
    PropertyPrice,
)
from ...core.utils.s3 import generate_presigned_url
from ...services.property.service import PropertyService
from ..dependencies import get_property_service

router = APIRouter(prefix="/properties", tags=["Properties"])


@router.get("", response_model=PropertyListResponse)
async def search_properties(
    service: Annotated[PropertyService, Depends(get_property_service)],
    query: Optional[str] = Query(None, description="Full-text search term"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Page size"),
    cities: Optional[str] = Query(None, description="Comma-separated city filters"),
    states: Optional[str] = Query(None, description="Comma-separated state filters"),
    postal_codes: Optional[str] = Query(None, description="Comma-separated postal code filters"),
    min_bedrooms: Optional[int] = Query(None, ge=0, description="Minimum number of bedrooms"),
    max_bedrooms: Optional[int] = Query(None, ge=0, description="Maximum number of bedrooms"),
    min_bathrooms: Optional[int] = Query(None, ge=0, description="Minimum number of bathrooms"),
    max_bathrooms: Optional[int] = Query(None, ge=0, description="Maximum number of bathrooms"),
    sort_by: Optional[str] = Query(None, description="Sort field: price, bedrooms, bathrooms, created_at, updated_at"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc or desc"),
    has_photo: Optional[bool] = Query(None, description="Only return properties with a primary photo"),
) -> Any:
    filters: Dict[str, Any] = {}
    if cities:
        filters["city"] = [c.strip().lower() for c in cities.split(",")]
    if states:
        filters["state_or_province"] = [s.strip().lower() for s in states.split(",")]
    if postal_codes:
        filters["postal_code"] = [p.strip().lower() for p in postal_codes.split(",")]

    ranges: Dict[str, Dict[str, int]] = {}
    if min_bedrooms is not None or max_bedrooms is not None:
        r: Dict[str, int] = {}
        if min_bedrooms is not None:
            r["gte"] = min_bedrooms
        if max_bedrooms is not None:
            r["lte"] = max_bedrooms
        ranges["bedrooms_total"] = r
    if min_bathrooms is not None or max_bathrooms is not None:
        r2: Dict[str, int] = {}
        if min_bathrooms is not None:
            r2["gte"] = min_bathrooms
        if max_bathrooms is not None:
            r2["lte"] = max_bathrooms
        ranges["bathrooms_total_integer"] = r2

    sort: list[Dict[str, str]] | None = None
    if sort_by:
        sort_field_map = {
            "price": "list_price",
            "bedrooms": "bedrooms_total",
            "bathrooms": "bathrooms_total_integer",
            "created_at": "created_at",
            "updated_at": "updated_at",
        }
        es_field = sort_field_map.get(sort_by)
        if es_field:
            order = sort_order if sort_order in ("asc", "desc") else "desc"
            sort = [{es_field: order}]

    result = await service.search_properties(
        query=query, page=page, limit=limit, filters=filters, ranges=ranges, sort=sort,
        has_photo=has_photo,
    )
    return result


@router.get("/suggest", response_model=PropertySuggestResponse)
async def suggest_properties(
    service: Annotated[PropertyService, Depends(get_property_service)],
    query: str = Query(..., min_length=1, description="Partial search term"),
    limit: int = Query(10, ge=1, le=25, description="Maximum number of suggestions"),
) -> Any:
    suggestions = await service.suggest_properties(query=query, limit=limit)
    return {"suggestions": suggestions}


@router.get("/{listing_key}", response_model=PropertyDetailResponse)
async def get_property(
    listing_key: str,
    db: AsyncSession = Depends(async_get_db),
) -> Any:
    property = await crud_property.get(db, listing_key=listing_key)
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    # Query S3-backed media from property_media table
    media_stmt = (
        select(PropertyMediaModel)
        .where(PropertyMediaModel.property_id == listing_key)
        .order_by(PropertyMediaModel.order)
    )
    media_result = await db.execute(media_stmt)
    media_rows = media_result.scalars().all()
    media_items = [
        PropertyMediaItem(
            url=generate_presigned_url(row.s3_path),
            kind=row.kind,
            order=row.order,
            description=row.description,
        )
        for row in media_rows
    ]

    raw_photo_key = property.get("primary_photo")
    primary_photo_url = generate_presigned_url(raw_photo_key)
    return PropertyDetailResponse(
        id=property["listing_key"],
        name=property.get("unparsed_address"),
        description=property.get("public_remarks"),
        address=property.get("unparsed_address"),
        city=property.get("city"),
        state=property.get("state_or_province"),
        postal_code=property.get("postal_code"),
        bedrooms=property.get("bedrooms_total"),
        bathrooms=property.get("bathrooms_total_integer"),
        area=property.get("living_area"),
        amenities=property.get("interior_features") or [],
        media=media_items,
        primary_photo=primary_photo_url,
        latitude=property.get("latitude"),
        longitude=property.get("longitude"),
        price=PropertyPrice(
            amount=property.get("list_price"),
            currency="USD",
            period="sale",
        ),
        rating=0,
    )
