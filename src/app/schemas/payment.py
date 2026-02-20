from datetime import datetime

from pydantic import BaseModel, EmailStr


class PaymentPlan(BaseModel):
    id: int
    code: str
    product_code: str
    version: int
    amount_cents: int
    currency: str
    billing_interval: str
    created_at: datetime
    updated_at: datetime | None = None


class ListPaymentPlansResponse(BaseModel):
    plans: list[PaymentPlan]


class CreatePaymentPlanRequest(BaseModel):
    code: str
    product_code: str
    amount_cents: int
    currency: str
    billing_interval: str


class UpdatePaymentPlanRequest(BaseModel):
    code: str
    product_code: str
    version: int
    amount_cents: int
    currency: str
    billing_interval: str


class DeletePaymentPlanResponse(BaseModel):
    id: int


class CheckoutRequest(BaseModel):
    customer_email: EmailStr


class CheckoutResponse(BaseModel):
    url: str


class SubscriptionSummary(BaseModel):
    id: str
    status: str
    current_period_end: datetime
    current_period_start: datetime
    cancel_at_period_end: bool
    price_id: str


class SubscriptionSnapshot(BaseModel):
    user_id: int
    customer_id: str
    subscriptions: list[SubscriptionSummary]
    last_synced_at: datetime


class SyncStripeCustomerRequest(BaseModel):
    customer_id: str
