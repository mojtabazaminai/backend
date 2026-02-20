from typing import Annotated

from fastapi import APIRouter, Depends

from ...schemas.auth import Envelope
from ...schemas.subscription import ListPlansResponse
from ...services.subscription.service import SubscriptionService
from ..dependencies import get_subscription_service

router = APIRouter(prefix="/subscription", tags=["Subscription"])


@router.get("/plans", response_model=Envelope[ListPlansResponse])
async def list_plans(
    service: Annotated[SubscriptionService, Depends(get_subscription_service)],
) -> Envelope[ListPlansResponse]:
    plans = await service.list_plans()
    return Envelope(data=ListPlansResponse(plans=plans))
