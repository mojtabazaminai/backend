from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from ...schemas.auth import Envelope
from ...schemas.payment import CheckoutRequest, CheckoutResponse, SubscriptionSnapshot
from ...services.payment.service import PaymentService
from ..dependencies import get_current_user, get_payment_service

router = APIRouter(prefix="/payment", tags=["Payment"])


@router.post("/checkout", response_model=Envelope[CheckoutResponse])
async def checkout(
    payload: CheckoutRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[PaymentService, Depends(get_payment_service)],
) -> Envelope[CheckoutResponse]:
    try:
        result = await service.generate_checkout_session(
            user_id=current_user["id"],
            customer_email=payload.customer_email,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return Envelope(data=result)


@router.post("/stripe/callback", response_model=Envelope[SubscriptionSnapshot])
async def stripe_callback(
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[PaymentService, Depends(get_payment_service)],
) -> Envelope[SubscriptionSnapshot]:
    try:
        snapshot = await service.sync_after_success(user_id=current_user["id"])
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return Envelope(data=snapshot)

