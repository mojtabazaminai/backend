from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .notification import NotificationPayload


class NotificationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    caller: str | None = None
    user_id: int | None = None
    channel: str | None = None
    deduplication_id: str | None = None
    payload: NotificationPayload | None = None
    status: str | None = None
    send_at: datetime | None = None
    metadata_: dict[str, Any] | None = Field(default=None, alias="metadata")


class PaymentPlanCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    product_code: str
    version: int
    amount_cents: int
    currency: str
    billing_interval: str


class PaymentPlanUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str | None = None
    product_code: str | None = None
    version: int | None = None
    amount_cents: int | None = None
    currency: str | None = None
    billing_interval: str | None = None


class UserPaymentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: int
    customer_id: str
    provider: str
    last_synced_at: datetime | None = None


class UserPaymentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: int | None = None
    customer_id: str | None = None
    provider: str | None = None
    last_synced_at: datetime | None = None


class PaymentSubscriptionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: int
    customer_id: str
    subscription_id: str
    status: str
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    price_id: str
    synced_at: datetime | None = None


class PaymentSubscriptionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: int | None = None
    customer_id: str | None = None
    subscription_id: str | None = None
    status: str | None = None
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    cancel_at_period_end: bool | None = None
    price_id: str | None = None
    synced_at: datetime | None = None


class SubscriptionPlanCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tier: str
    display_name: str
    payment_plan_id: int
    payment_plan_code: str
    product_code: str
    amount_cents: int
    billing_interval: str
    soft_usage_limit: int = 0
    hard_usage_limit: int = 0
    features: list[str] = Field(default_factory=list)
    currency: str = "USD"


class SubscriptionPlanUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tier: str | None = None
    display_name: str | None = None
    payment_plan_id: int | None = None
    payment_plan_code: str | None = None
    product_code: str | None = None
    amount_cents: int | None = None
    billing_interval: str | None = None
    soft_usage_limit: int | None = None
    hard_usage_limit: int | None = None
    features: list[str] | None = None
    currency: str | None = None


class UserSubscriptionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: int
    plan_id: int
    ended_at: datetime | None = None
    canceled_at: datetime | None = None
    started_at: datetime | None = None
    monthly_listing_usage: int = 0


class UserSubscriptionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: int | None = None
    plan_id: int | None = None
    ended_at: datetime | None = None
    canceled_at: datetime | None = None
    started_at: datetime | None = None
    monthly_listing_usage: int | None = None


class UserSubscriptionUsageCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_subscription_id: int
    user_id: int
    property_id: str


class UserSubscriptionUsageUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_subscription_id: int | None = None
    user_id: int | None = None
    property_id: str | None = None
