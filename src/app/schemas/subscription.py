from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UsageItem(BaseModel):
    property_id: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    primary_photo: Optional[str] = None
    created_at: datetime


class UsageReportResponse(BaseModel):
    total: int
    page: int
    limit: int
    items: list[UsageItem]


class PlanPayment(BaseModel):
    payment_plan_id: int
    payment_plan_code: str
    product_code: str
    amount_cents: int
    currency: str
    billing_interval: str


class Plan(BaseModel):
    tier: str
    display_name: str
    usage_limit: int
    features: list[str]
    payment: PlanPayment


class ListPlansResponse(BaseModel):
    plans: list[Plan]
