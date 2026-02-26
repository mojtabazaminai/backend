from fastapi import APIRouter

from .users import router as users_router
from .health import router as health_router
from .properties import router as properties_router
from .reports import router as reports_router
from .subscription import router as subscription_router
from .payment import router as payment_router
from .cma import router as cma_router


router = APIRouter(prefix="/v1")
router.include_router(health_router)
router.include_router(users_router)
router.include_router(properties_router)
router.include_router(reports_router)
router.include_router(subscription_router)
router.include_router(payment_router)
router.include_router(cma_router)
