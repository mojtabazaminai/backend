import uuid
from datetime import UTC, datetime, timedelta
from typing import Iterable

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.config import settings
from ...models.payment import PaymentPlan, PaymentSubscription, UserPayment
from ...schemas.payment import (
    CheckoutResponse,
    PaymentPlan as PaymentPlanSchema,
    SubscriptionSnapshot,
    SubscriptionSummary,
)


class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_payment_plans(self, product_codes: Iterable[str] | None = None) -> list[PaymentPlanSchema]:
        stmt = select(PaymentPlan).order_by(PaymentPlan.product_code.asc(), PaymentPlan.version.desc())
        if product_codes:
            stmt = stmt.where(PaymentPlan.product_code.in_(list(product_codes)))
        result = await self.db.execute(stmt)
        rows = result.scalars().all()

        seen: set[str] = set()
        plans: list[PaymentPlanSchema] = []
        for plan in rows:
            if plan.product_code in seen:
                continue
            plans.append(self._map_plan(plan))
            seen.add(plan.product_code)

        return plans

    async def get_payment_plan(self, plan_id: int) -> PaymentPlanSchema:
        result = await self.db.execute(select(PaymentPlan).where(PaymentPlan.id == plan_id))
        plan = result.scalar_one_or_none()
        if not plan:
            raise ValueError("payment plan not found")
        return self._map_plan(plan)

    async def create_payment_plan(
        self,
        code: str,
        product_code: str,
        amount_cents: int,
        currency: str,
        billing_interval: str,
    ) -> PaymentPlanSchema:
        version = await self._next_plan_version(product_code)
        plan = PaymentPlan(
            code=code,
            product_code=product_code,
            version=version,
            amount_cents=amount_cents,
            currency=currency,
            billing_interval=billing_interval,
        )
        self.db.add(plan)
        await self.db.commit()
        await self.db.refresh(plan)
        return self._map_plan(plan)

    async def update_payment_plan(
        self,
        plan_id: int,
        code: str,
        product_code: str,
        version: int,
        amount_cents: int,
        currency: str,
        billing_interval: str,
    ) -> PaymentPlanSchema:
        result = await self.db.execute(select(PaymentPlan).where(PaymentPlan.id == plan_id))
        plan = result.scalar_one_or_none()
        if not plan:
            raise ValueError("payment plan not found")
        plan.code = code
        plan.product_code = product_code
        plan.version = version
        plan.amount_cents = amount_cents
        plan.currency = currency
        plan.billing_interval = billing_interval
        await self.db.commit()
        await self.db.refresh(plan)
        return self._map_plan(plan)

    async def delete_payment_plan(self, plan_id: int) -> int:
        result = await self.db.execute(select(PaymentPlan).where(PaymentPlan.id == plan_id))
        plan = result.scalar_one_or_none()
        if not plan:
            raise ValueError("payment plan not found")
        await self.db.delete(plan)
        await self.db.commit()
        return plan_id

    async def generate_checkout_session(self, user_id: int, customer_email: str) -> CheckoutResponse:
        if user_id <= 0:
            raise ValueError("user_id is required")
        if not settings.PAYMENT_STRIPE_PRICE_ID:
            raise ValueError("stripe price id is not configured")
        if not settings.PAYMENT_STRIPE_SUCCESS_URL or not settings.PAYMENT_STRIPE_CANCEL_URL:
            raise ValueError("stripe redirect urls are not configured")

        customer_id = await self._ensure_customer(user_id, customer_email)

        url = f"{settings.PAYMENT_MOCK_CHECKOUT_BASE_URL}?customer_id={customer_id}"
        return CheckoutResponse(url=url)

    async def sync_after_success(self, user_id: int) -> SubscriptionSnapshot:
        customer_id = await self._lookup_customer(user_id)
        return await self._sync_customer(user_id, customer_id)

    async def sync_stripe_customer(self, customer_id: str) -> SubscriptionSnapshot:
        user_id = await self._lookup_user(customer_id)
        return await self._sync_customer(user_id, customer_id)

    async def _next_plan_version(self, product_code: str) -> int:
        result = await self.db.execute(
            select(func.max(PaymentPlan.version)).where(PaymentPlan.product_code == product_code)
        )
        max_version = result.scalar_one_or_none() or 0
        return int(max_version) + 1

    async def _ensure_customer(self, user_id: int, customer_email: str) -> str:
        result = await self.db.execute(select(UserPayment).where(UserPayment.user_id == user_id))
        binding = result.scalar_one_or_none()
        if binding:
            return binding.customer_id
        if not customer_email:
            raise ValueError("customer_email is required")
        customer_id = f"mock_cus_{uuid.uuid4().hex[:12]}"
        binding = UserPayment(
            user_id=user_id,
            customer_id=customer_id,
            provider=settings.PAYMENT_PROVIDER,
        )
        self.db.add(binding)
        await self.db.commit()
        await self.db.refresh(binding)
        return binding.customer_id

    async def _lookup_customer(self, user_id: int) -> str:
        result = await self.db.execute(select(UserPayment).where(UserPayment.user_id == user_id))
        binding = result.scalar_one_or_none()
        if not binding:
            raise ValueError("stripe customer binding not found")
        return binding.customer_id

    async def _lookup_user(self, customer_id: str) -> int:
        result = await self.db.execute(select(UserPayment).where(UserPayment.customer_id == customer_id))
        binding = result.scalar_one_or_none()
        if not binding:
            raise ValueError("stripe customer binding not found")
        return binding.user_id

    async def _sync_customer(self, user_id: int, customer_id: str) -> SubscriptionSnapshot:
        now = datetime.now(UTC)
        summary = SubscriptionSummary(
            id=f"mock_sub_{uuid.uuid4().hex[:12]}",
            status="active",
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            cancel_at_period_end=False,
            price_id=settings.PAYMENT_STRIPE_PRICE_ID,
        )

        await self.db.execute(
            delete(PaymentSubscription).where(
                PaymentSubscription.user_id == user_id,
                PaymentSubscription.customer_id == customer_id,
            )
        )
        self.db.add(
            PaymentSubscription(
                user_id=user_id,
                customer_id=customer_id,
                subscription_id=summary.id,
                status=summary.status,
                current_period_start=summary.current_period_start,
                current_period_end=summary.current_period_end,
                cancel_at_period_end=summary.cancel_at_period_end,
                price_id=summary.price_id,
                synced_at=now,
            )
        )

        result = await self.db.execute(select(UserPayment).where(UserPayment.user_id == user_id))
        binding = result.scalar_one_or_none()
        if binding:
            binding.last_synced_at = now

        await self.db.commit()

        return SubscriptionSnapshot(
            user_id=user_id,
            customer_id=customer_id,
            subscriptions=[summary],
            last_synced_at=now,
        )

    def _map_plan(self, plan: PaymentPlan) -> PaymentPlanSchema:
        return PaymentPlanSchema(
            id=plan.id,
            code=plan.code,
            product_code=plan.product_code,
            version=plan.version,
            amount_cents=plan.amount_cents,
            currency=plan.currency,
            billing_interval=plan.billing_interval,
            created_at=plan.created_at,
            updated_at=plan.updated_at,
        )
