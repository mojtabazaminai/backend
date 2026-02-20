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

    # Map SQLAlchemy model to Pydantic schema
    return PropertyDetailResponse(
        id=property.listing_key,
        name=property.unparsed_address,
        description=property.public_remarks,
        address=property.unparsed_address,
        city=property.city,
        state=property.state_or_province,
        postal_code=property.postal_code,
        bedrooms=property.bedrooms_total,
        bathrooms=property.bathrooms_total_integer,
        area=property.living_area,
        amenities=property.interior_features or [],
        images=[m.get("MediaURL", "") for m in property.media] if property.media else [],
        price=PropertyPrice(
            amount=property.list_price,
            currency="USD",
            period="sale",
        ),
        rating=0, 
    )
