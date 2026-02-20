from pydantic import BaseModel


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
