from typing import Annotated, Any

from elasticsearch import AsyncElasticsearch
from fastapi import Depends, HTTPException, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.db.database import async_get_db
from ..core.exceptions.http_exceptions import ForbiddenException, RateLimitException, UnauthorizedException
from ..core.logger import logging
from ..core.search.elasticsearch import es_client
from ..core.security import TokenType, verify_token
from ..core.utils.cache import async_get_redis
from ..core.utils.rate_limit import rate_limiter, sanitize_path
from ..crud.crud_users import crud_users
from ..services.users.service import UserService
from ..services.property.service import PropertyService
from ..services.subscription.service import SubscriptionService
from ..services.payment.service import PaymentService

logger = logging.getLogger(__name__)

DEFAULT_LIMIT = settings.DEFAULT_RATE_LIMIT_LIMIT
DEFAULT_PERIOD = settings.DEFAULT_RATE_LIMIT_PERIOD


async def get_es_client() -> AsyncElasticsearch:
    return es_client.get_client()


async def get_property_service(
    es: Annotated[AsyncElasticsearch, Depends(get_es_client)],
) -> PropertyService:
    return PropertyService(es)


async def get_users_service(
    db: Annotated[AsyncSession, Depends(async_get_db)],
    redis: Annotated[Redis, Depends(async_get_redis)],
) -> UserService:
    return UserService(db, redis)


async def get_subscription_service(
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> SubscriptionService:
    return SubscriptionService(db)


async def get_payment_service(
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> PaymentService:
    return PaymentService(db)


async def get_current_user(
    request: Request,
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> dict[str, Any]:
    # Check Authorization header first
    token = request.headers.get("Authorization")
    if token:
        token_type, _, token_value = token.partition(" ")
        if token_type.lower() == "bearer" and token_value:
            token = token_value
        else:
            token = None
    
    # Fallback to cookie
    if not token:
        token = request.cookies.get("access_token")

    if not token:
        raise UnauthorizedException("User not authenticated.")

    token_data = await verify_token(token, TokenType.ACCESS)
    if token_data is None:
        raise UnauthorizedException("User not authenticated.")

    if "@" in token_data.username_or_email:
        user = await crud_users.get(db=db, email=token_data.username_or_email)
    else:
        user = await crud_users.get(db=db, username=token_data.username_or_email)

    if user:
        return user

    raise UnauthorizedException("User not authenticated.")


async def get_optional_user(request: Request, db: AsyncSession = Depends(async_get_db)) -> dict | None:
    try:
        return await get_current_user(request, db)
    except UnauthorizedException:
        return None
    except HTTPException as http_exc:
        if http_exc.status_code != 401:
            logger.error(f"Unexpected HTTPException in get_optional_user: {http_exc.detail}")
        return None
    except Exception as exc:
        logger.error(f"Unexpected error in get_optional_user: {exc}")
        return None


async def get_current_superuser(current_user: Annotated[dict, Depends(get_current_user)]) -> dict:
    if not current_user["is_superuser"]:
        raise ForbiddenException("You do not have enough privileges.")

    return current_user


async def rate_limit_dependency(
    request: Request,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    user: Annotated[dict | None, Depends(get_optional_user)],
) -> None:
    """Rate limit dependency using env config (DEFAULT_RATE_LIMIT_LIMIT and DEFAULT_RATE_LIMIT_PERIOD)."""
    if hasattr(request.app.state, "initialization_complete"):
        await request.app.state.initialization_complete.wait()

    path = sanitize_path(request.url.path)

    if user:
        user_id = user["id"]
    else:
        user_id = request.client.host if request.client else "unknown"

    is_limited = await rate_limiter.is_rate_limited(
        db=db, user_id=user_id, path=path, limit=DEFAULT_LIMIT, period=DEFAULT_PERIOD
    )
    if is_limited:
        raise RateLimitException("Rate limit exceeded.")
