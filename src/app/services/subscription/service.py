from datetime import UTC, datetime

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.utils.s3 import generate_presigned_url
from ...models.property import Property
from ...models.subscription import (
    SubscriptionPlan,
    UserSubscription,
    UserSubscriptionUsage,
)
from ...schemas.auth import SubscriptionSummary
from ...schemas.subscription import Plan, PlanPayment, UsageItem, UsageReportResponse


class SubscriptionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_plans(self) -> list[Plan]:
        result = await self.db.execute(
            select(SubscriptionPlan).order_by(SubscriptionPlan.id)
        )
        plans = result.scalars().all()
        return [self._map_plan(plan) for plan in plans]

    async def get_summary(self, user_id: int) -> SubscriptionSummary:
        if user_id <= 0:
            return self._default_summary()

        sub_with_plan = await self._get_active_subscription(user_id)
        if not sub_with_plan:
            return self._default_summary()

        subscription, plan = sub_with_plan
        if not plan:
            return self._default_summary()

        return self._build_summary(subscription, plan)

    async def add_usage(self, user_id: int, property_id: str) -> bool:
        if user_id <= 0 or not property_id:
            return False

        sub_with_plan = await self._get_active_subscription(user_id)
        if not sub_with_plan:
            raise ValueError("no active subscription")

        subscription, plan = sub_with_plan
        if not plan:
            raise ValueError("no active subscription")

        used = subscription.monthly_listing_usage or 0
        hard_limit = plan.hard_usage_limit or 0
        if hard_limit > 0 and used >= hard_limit:
            raise ValueError("usage limit reached")

        existing = await self.db.execute(
            select(UserSubscriptionUsage).where(
                UserSubscriptionUsage.user_subscription_id == subscription.id,
                UserSubscriptionUsage.user_id == user_id,
                UserSubscriptionUsage.property_id == property_id,
            )
        )
        if existing.scalar_one_or_none():
            return False

        usage = UserSubscriptionUsage(
            user_subscription_id=subscription.id,
            user_id=user_id,
            property_id=property_id,
        )
        self.db.add(usage)
        subscription.monthly_listing_usage = used + 1
        await self.db.commit()
        return True

    async def get_usage_report(
        self, user_id: int, page: int = 1, limit: int = 20
    ) -> UsageReportResponse:
        offset = (page - 1) * limit

        count_stmt = (
            select(func.count())
            .select_from(UserSubscriptionUsage)
            .where(UserSubscriptionUsage.user_id == user_id)
        )
        total = (await self.db.execute(count_stmt)).scalar() or 0

        stmt = (
            select(
                UserSubscriptionUsage.property_id,
                UserSubscriptionUsage.created_at,
                Property.unparsed_address,
                Property.city,
                Property.state_or_province,
                Property.primary_photo,
            )
            .outerjoin(Property, UserSubscriptionUsage.property_id == Property.listing_key)
            .where(UserSubscriptionUsage.user_id == user_id)
            .order_by(UserSubscriptionUsage.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        rows = (await self.db.execute(stmt)).all()

        items = []
        for row in rows:
            photo_url = generate_presigned_url(row.primary_photo) if row.primary_photo else None
            items.append(UsageItem(
                property_id=row.property_id,
                address=row.unparsed_address,
                city=row.city,
                state=row.state_or_province,
                primary_photo=photo_url,
                created_at=row.created_at,
            ))

        return UsageReportResponse(total=total, page=page, limit=limit, items=items)

    async def _get_active_subscription(
        self, user_id: int
    ) -> tuple[UserSubscription, SubscriptionPlan | None] | None:
        now = datetime.now(UTC)
        active_stmt = (
            select(UserSubscription, SubscriptionPlan)
            .join(SubscriptionPlan, UserSubscription.plan_id == SubscriptionPlan.id)
            .where(
                UserSubscription.user_id == user_id,
                or_(UserSubscription.ended_at.is_(None), UserSubscription.ended_at > now),
            )
            .order_by(UserSubscription.ended_at.asc().nulls_last())
        )
        result = await self.db.execute(active_stmt)
        row = result.first()
        if row:
            return row[0], row[1]

        latest_stmt = (
            select(UserSubscription, SubscriptionPlan)
            .join(SubscriptionPlan, UserSubscription.plan_id == SubscriptionPlan.id, isouter=True)
            .where(UserSubscription.user_id == user_id)
            .order_by(UserSubscription.ended_at.desc().nulls_last())
        )
        result = await self.db.execute(latest_stmt)
        row = result.first()
        if row:
            return row[0], row[1]

        return None

    def _map_plan(self, plan: SubscriptionPlan) -> Plan:
        return Plan(
            tier=plan.tier,
            display_name=plan.display_name,
            usage_limit=plan.hard_usage_limit,
            features=plan.features,
            payment=PlanPayment(
                payment_plan_id=plan.payment_plan_id,
                payment_plan_code=plan.payment_plan_code,
                product_code=plan.product_code,
                amount_cents=plan.amount_cents,
                currency=plan.currency,
                billing_interval=plan.billing_interval,
            ),
        )

    def _build_summary(
        self, subscription: UserSubscription, plan: SubscriptionPlan
    ) -> SubscriptionSummary:
        used = subscription.monthly_listing_usage or 0
        soft_limit = plan.soft_usage_limit or 0
        hard_limit = plan.hard_usage_limit or 0
        soft_reached = soft_limit > 0 and used >= soft_limit
        hard_reached = hard_limit > 0 and used >= hard_limit

        if hard_reached:
            limit_status = "at_limit"
        elif soft_reached:
            limit_status = "near_limit"
        else:
            limit_status = "normal"

        now = datetime.now(UTC)
        ended_at = subscription.ended_at
        remaining_days = 0
        if ended_at and ended_at > now:
            remaining_days = (ended_at - now).days

        renewal_status = "not_renewing"
        if ended_at:
            if ended_at <= now:
                renewal_status = "expired"
            elif subscription.canceled_at:
                renewal_status = "not_renewing"
            else:
                renewal_status = "renewing"

        remaining = 0
        if hard_limit > 0:
            remaining = max(hard_limit - used, 0)

        return SubscriptionSummary(
            tier=plan.tier,
            used=used,
            remaining=remaining,
            remaining_days=remaining_days,
            limit_status=limit_status,
            renewal_status=renewal_status,
        )

    def _default_summary(self) -> SubscriptionSummary:
        return SubscriptionSummary(
            tier="basic",
            used=0,
            remaining=0,
            remaining_days=0,
            limit_status="at_limit",
            renewal_status="not_renewing",
        )
