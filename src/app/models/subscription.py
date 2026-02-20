from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, String, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db.database import Base


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plan"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, init=False)
    tier: Mapped[str] = mapped_column(String, nullable=False)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    payment_plan_id: Mapped[int] = mapped_column(Integer, nullable=False)
    payment_plan_code: Mapped[str] = mapped_column(String, nullable=False)
    product_code: Mapped[str] = mapped_column(String, nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    billing_interval: Mapped[str] = mapped_column(String, nullable=False)
    soft_usage_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    hard_usage_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    features: Mapped[list[str]] = mapped_column(JSON, nullable=False, default_factory=list)
    currency: Mapped[str] = mapped_column(String, nullable=False, default="USD")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default_factory=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None,
        onupdate=lambda: datetime.now(UTC),
    )


class UserSubscription(Base):
    __tablename__ = "user_subscription"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, init=False)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    plan_id: Mapped[int] = mapped_column(ForeignKey("subscription_plan.id"), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default_factory=lambda: datetime.now(UTC),
    )
    monthly_listing_usage: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default_factory=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None,
        onupdate=lambda: datetime.now(UTC),
    )


class UserSubscriptionUsage(Base):
    __tablename__ = "user_subscription_usages"
    __table_args__ = (
        UniqueConstraint(
            "user_subscription_id",
            "user_id",
            "property_id",
            name="uq_subscription_usage_user_property",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, init=False)
    user_subscription_id: Mapped[int] = mapped_column(
        ForeignKey("user_subscription.id"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    property_id: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default_factory=lambda: datetime.now(UTC),
    )
