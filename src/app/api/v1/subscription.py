from typing import Annotated

from fastapi import APIRouter, Depends, Query

from ...schemas.auth import Envelope
from ...schemas.subscription import ListPlansResponse, UsageReportResponse
from ...services.subscription.service import SubscriptionService
from ..dependencies import get_current_user, get_subscription_service

router = APIRouter(prefix="/subscription", tags=["Subscription"])


@router.get("/plans", response_model=Envelope[ListPlansResponse])
async def list_plans(
    service: Annotated[SubscriptionService, Depends(get_subscription_service)],
) -> Envelope[ListPlansResponse]:
    plans = await service.list_plans()
    return Envelope(data=ListPlansResponse(plans=plans))


@router.get("/usage", response_model=Envelope[UsageReportResponse])
async def usage_report(
    service: Annotated[SubscriptionService, Depends(get_subscription_service)],
    current_user: Annotated[dict, Depends(get_current_user)],
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Page size"),
) -> Envelope[UsageReportResponse]:
    report = await service.get_usage_report(
        user_id=current_user["id"], page=page, limit=limit
    )
    return Envelope(data=report)
