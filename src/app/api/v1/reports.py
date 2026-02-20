from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.db.database import async_get_db
from ...crud import crud_property
from ...schemas.report import (
    Indicator,
    SimilarListings,
    Spectrum,
    UpgradeImpact,
)
from ...services.report import report_service
from ...services.subscription.service import SubscriptionService
from ..dependencies import get_optional_user, get_subscription_service

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/similar-listings", response_model=SimilarListings)
async def get_similar_listings(
    listing_key: str = Query(..., description="Listing key to build the similar listings for"),
    db: AsyncSession = Depends(async_get_db),
    current_user: dict | None = Depends(get_optional_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
) -> Any:
    property_data = await crud_property.get(db, listing_key=listing_key)
    if not property_data:
        raise HTTPException(status_code=404, detail="Property not found")

    if current_user:
        try:
            await subscription_service.add_usage(
                user_id=current_user["id"], property_id=listing_key
            )
        except ValueError as exc:
            raise HTTPException(status_code=412, detail=str(exc)) from exc

    return await report_service.get_similar_listings(listing_key, property_data)


@router.get("/spectrum", response_model=Spectrum)
async def get_spectrum(
    listing_key: str = Query(..., description="Listing key to build the spectrum for"),
    indicator: Indicator = Query(Indicator.SALES_PROBABILITY, description="Indicator type"),
    db: AsyncSession = Depends(async_get_db),
    current_user: dict | None = Depends(get_optional_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
) -> Any:
    property_data = await crud_property.get(db, listing_key=listing_key)
    if not property_data:
        raise HTTPException(status_code=404, detail="Property not found")

    if current_user:
        try:
            await subscription_service.add_usage(
                user_id=current_user["id"], property_id=listing_key
            )
        except ValueError as exc:
            raise HTTPException(status_code=412, detail=str(exc)) from exc

    return await report_service.get_spectrum(listing_key, indicator, property_data)


@router.get("/upgrade-impact", response_model=UpgradeImpact)
async def get_upgrade_impact(
    listing_key: str = Query(..., description="Listing key for upgrade impact analysis"),
    db: AsyncSession = Depends(async_get_db),
    current_user: dict | None = Depends(get_optional_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
) -> Any:
    property_data = await crud_property.get(db, listing_key=listing_key)
    if not property_data:
        raise HTTPException(status_code=404, detail="Property not found")

    if current_user:
        try:
            await subscription_service.add_usage(
                user_id=current_user["id"], property_id=listing_key
            )
        except ValueError as exc:
            raise HTTPException(status_code=412, detail=str(exc)) from exc

    return await report_service.get_upgrade_impact(listing_key, property_data)
