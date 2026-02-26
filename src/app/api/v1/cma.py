from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.db.database import async_get_db
from ...schemas.cma import (
    ComparablesRequest,
    ComparablesResponse,
    ReportRequest,
    ReportResponse,
)
from ...services.cma import cma_service
from ...services.subscription.service import SubscriptionService
from ..dependencies import get_current_user, get_subscription_service

router = APIRouter(prefix="/cma", tags=["CMA"])


@router.post("/comparables", response_model=ComparablesResponse)
async def find_comparables(
    body: ComparablesRequest,
    db: AsyncSession = Depends(async_get_db),
    current_user: dict = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
) -> Any:
    if body.subject_listing_key:
        try:
            await subscription_service.add_usage(
                user_id=current_user["id"], property_id=body.subject_listing_key
            )
        except ValueError as exc:
            raise HTTPException(status_code=412, detail=str(exc)) from exc

    return await cma_service.find_comparables(body.model_dump(exclude_none=True))


@router.post("/reports", response_model=ReportResponse)
async def generate_report(
    body: ReportRequest,
    db: AsyncSession = Depends(async_get_db),
    current_user: dict = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
) -> Any:
    if body.subject_listing_key:
        try:
            await subscription_service.add_usage(
                user_id=current_user["id"], property_id=body.subject_listing_key
            )
        except ValueError as exc:
            raise HTTPException(status_code=412, detail=str(exc)) from exc

    return await cma_service.generate_report(body)
