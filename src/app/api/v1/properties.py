from typing import Annotated, Any, Dict, Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.db.database import async_get_db
from ...crud import crud_property
from ...schemas.property import (
    PropertyDetailResponse,
    PropertyListResponse,
    PropertySuggestResponse,
    PropertyPrice,
)
from ...core.utils.s3 import generate_presigned_url, get_s3_address
from ...services.property.service import PropertyService
from ...services.subscription.service import SubscriptionService
from ..dependencies import get_optional_user, get_property_service, get_subscription_service

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
) -> Any:
    filters: Dict[str, Any] = {}
    if cities:
        filters["city"] = [c.strip().lower() for c in cities.split(",")]
    if states:
        filters["state_or_province"] = [s.strip().lower() for s in states.split(",")]
    if postal_codes:
        filters["postal_code"] = [p.strip().lower() for p in postal_codes.split(",")]

    result = await service.search_properties(
        query=query, page=page, limit=limit, filters=filters
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
    current_user: dict | None = Depends(get_optional_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
) -> Any:
    property = await crud_property.get(db, listing_key=listing_key)
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    if current_user:
        try:
            await subscription_service.add_usage(
                user_id=current_user["id"], property_id=listing_key
            )
        except ValueError as exc:
            raise HTTPException(status_code=412, detail=str(exc)) from exc

    # Map dict to Pydantic schema (FastCRUD .get() returns a dict)
    media = property.get("media") or []
    raw_photo_key = property.get("primary_photo")
    primary_photo_url = generate_presigned_url(raw_photo_key)
    primary_photo_s3 = get_s3_address(raw_photo_key)
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
        images=[m.get("MediaURL", "") for m in media],
        primary_photo=primary_photo_url,
        primary_photo_s3_address=primary_photo_s3,
        price=PropertyPrice(
            amount=property.get("list_price"),
            currency="USD",
            period="sale",
        ),
        rating=0,
    )
