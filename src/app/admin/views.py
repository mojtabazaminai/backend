from crudadmin import CRUDAdmin
from crudadmin.admin_interface.model_view import PasswordTransformer

from ..core.security import get_password_hash
from ..models import (
    IngestCategory,
    IngestChain,
    IngestJob,
    IngestPointOfInterest,
    Notification,
    PaymentPlan,
    PaymentSubscription,
    Property,
    SocialLogin,
    SubscriptionPlan,
    User,
    UserPayment,
    UserSubscription,
    UserSubscriptionUsage,
)
from ..schemas.admin import (
    NotificationUpdate,
    PaymentPlanCreate,
    PaymentPlanUpdate,
    PaymentSubscriptionCreate,
    PaymentSubscriptionUpdate,
    SubscriptionPlanCreate,
    SubscriptionPlanUpdate,
    UserPaymentCreate,
    UserPaymentUpdate,
    UserSubscriptionCreate,
    UserSubscriptionUpdate,
    UserSubscriptionUsageCreate,
    UserSubscriptionUsageUpdate,
)
from ..schemas.ingest import (
    CategoryCreate,
    CategoryUpdate,
    ChainCreate,
    ChainUpdate,
    JobCreate,
    JobUpdate,
    PointOfInterestCreate,
    PointOfInterestUpdate,
)
from ..schemas.notification import NotificationCreate
from ..schemas.property import PropertyBase
from ..schemas.social_login import SocialLoginCreate, SocialLoginUpdate
from ..schemas.user import UserCreate, UserUpdate


def register_admin_views(admin: CRUDAdmin) -> None:
    """Register all models and their schemas with the admin interface."""
    password_transformer = PasswordTransformer(
        password_field="password",
        hashed_field="password_hash",
        hash_function=get_password_hash,
        required_fields=["name", "email"],
    )

    admin.add_view(
        model=User,
        create_schema=UserCreate,
        update_schema=UserUpdate,
        password_transformer=password_transformer,
    )
    admin.add_view(
        model=SocialLogin,
        create_schema=SocialLoginCreate,
        update_schema=SocialLoginUpdate,
    )
    admin.add_view(
        model=IngestCategory,
        create_schema=CategoryCreate,
        update_schema=CategoryUpdate,
    )
    admin.add_view(
        model=IngestChain,
        create_schema=ChainCreate,
        update_schema=ChainUpdate,
    )
    admin.add_view(
        model=IngestPointOfInterest,
        create_schema=PointOfInterestCreate,
        update_schema=PointOfInterestUpdate,
    )
    admin.add_view(
        model=IngestJob,
        create_schema=JobCreate,
        update_schema=JobUpdate,
    )
    admin.add_view(
        model=Notification,
        create_schema=NotificationCreate,
        update_schema=NotificationUpdate,
        allowed_actions={"view"},
    )
    admin.add_view(
        model=PaymentPlan,
        create_schema=PaymentPlanCreate,
        update_schema=PaymentPlanUpdate,
    )
    admin.add_view(
        model=UserPayment,
        create_schema=UserPaymentCreate,
        update_schema=UserPaymentUpdate,
        allowed_actions={"view"},
    )
    admin.add_view(
        model=PaymentSubscription,
        create_schema=PaymentSubscriptionCreate,
        update_schema=PaymentSubscriptionUpdate,
        allowed_actions={"view"},
    )
    admin.add_view(
        model=Property,
        create_schema=PropertyBase,
        update_schema=PropertyBase,
        select_schema=PropertyBase,
        allowed_actions={"view"},
    )
    admin.add_view(
        model=SubscriptionPlan,
        create_schema=SubscriptionPlanCreate,
        update_schema=SubscriptionPlanUpdate,
    )
    admin.add_view(
        model=UserSubscription,
        create_schema=UserSubscriptionCreate,
        update_schema=UserSubscriptionUpdate,
        allowed_actions={"view"},
    )
    admin.add_view(
        model=UserSubscriptionUsage,
        create_schema=UserSubscriptionUsageCreate,
        update_schema=UserSubscriptionUsageUpdate,
        allowed_actions={"view"},
    )
