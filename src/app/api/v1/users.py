from typing import Annotated, Any

from fastapi import APIRouter, Depends, Response, status

from ...core.security import create_access_token, create_refresh_token
from ...schemas.auth import (
    Envelope,
    LoginRequest,
    LoginResponse,
    MeResponse,
    OTPLoginRequest,
    OTPResponse,
    OTPVerifyRequest,
    PasswordResetRequest,
    PasswordResetVerifyRequest,
    ProfileUpdateRequest,
    ProviderCallbackRequest,
    ProviderClientIDResponse,
)
from ...schemas.user import UserUpdate
from ...services.subscription.service import SubscriptionService
from ...services.users.service import UserService
from ..dependencies import get_current_user, get_subscription_service, get_users_service

router = APIRouter(prefix="/users", tags=["users"])


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,  # Should be True in prod
        samesite="lax",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
    )


@router.get("/me", response_model=Envelope[MeResponse])
async def get_me(
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
    subscription_service: Annotated[
        SubscriptionService, Depends(get_subscription_service)
    ],
) -> Envelope[MeResponse]:
    # current_user is a dict from dependencies.py
    # We map it to MeResponse
    subscription = await subscription_service.get_summary(current_user["id"])
    return Envelope(
        data=MeResponse(
            name=current_user["name"],
            avatar=current_user.get("avatar_url"),
            subscription=subscription,
        )
    )


@router.patch("/profile", response_model=Envelope[MeResponse])
async def update_profile(
    request: ProfileUpdateRequest,
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
    users_service: Annotated[UserService, Depends(get_users_service)],
) -> Envelope[MeResponse]:
    # Map ProfileUpdateRequest to UserUpdate
    user_update = UserUpdate(
        name=request.name,
        first_name=request.first_name,
        last_name=request.last_name,
        avatar_url=request.avatar,
        password_hash=request.password,  # logic handles hashing
    )

    updated_user = await users_service.update_profile(
        user_id=current_user["id"],
        req=user_update,
        previous_password=request.previous_password,
    )

    return Envelope(
        data=MeResponse(
            name=updated_user.name,
            avatar=updated_user.avatar_url,
        )
    )


@router.post("/logout")
async def logout(response: Response) -> None:
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return None


@router.post("/email/login", response_model=Envelope[LoginResponse])
async def email_login(
    request: LoginRequest,
    response: Response,
    users_service: Annotated[UserService, Depends(get_users_service)],
) -> Envelope[LoginResponse]:
    user = await users_service.email_login(request)

    access_token = await create_access_token(data={"sub": user.email})
    refresh_token = await create_refresh_token(data={"sub": user.email})

    set_auth_cookies(response, access_token, refresh_token)

    return Envelope(
        data=LoginResponse(
            user_id=user.id,
            action="login",
        )
    )


@router.post("/email/otp", response_model=Envelope[OTPResponse])
async def email_otp_login(
    request: OTPLoginRequest,
    users_service: Annotated[UserService, Depends(get_users_service)],
) -> Envelope[OTPResponse]:
    otp_resp = await users_service.email_otp_login_init(request)
    return Envelope(data=otp_resp)


@router.post("/email/otp/verify", response_model=Envelope[LoginResponse])
async def email_otp_verify(
    request: OTPVerifyRequest,
    response: Response,
    users_service: Annotated[UserService, Depends(get_users_service)],
) -> Envelope[LoginResponse]:
    user, action = await users_service.email_otp_login_verify(request)

    access_token = await create_access_token(data={"sub": user.email})
    refresh_token = await create_refresh_token(data={"sub": user.email})

    set_auth_cookies(response, access_token, refresh_token)

    return Envelope(
        data=LoginResponse(
            user_id=user.id,
            action=action.value,
        )
    )


@router.post("/email/password-reset", response_model=Envelope[OTPResponse])
async def email_password_reset(
    request: PasswordResetRequest,
    users_service: Annotated[UserService, Depends(get_users_service)],
) -> Envelope[OTPResponse]:
    otp_resp = await users_service.password_reset_init(request)
    return Envelope(data=otp_resp)


@router.post("/email/password-reset/verify", response_model=Envelope[str])
async def email_password_reset_verify(
    request: PasswordResetVerifyRequest,
    response: Response,
    users_service: Annotated[UserService, Depends(get_users_service)],
) -> Envelope[str]:
    user = await users_service.password_reset_verify(request)

    access_token = await create_access_token(data={"sub": user.email})
    refresh_token = await create_refresh_token(data={"sub": user.email})

    set_auth_cookies(response, access_token, refresh_token)

    return Envelope(data="ok")


@router.get("/provider/{provider}", response_model=Envelope[ProviderClientIDResponse])
async def get_provider_data(
    provider: str,
    users_service: Annotated[UserService, Depends(get_users_service)],
) -> Envelope[ProviderClientIDResponse]:
    # Currently only google is supported
    if provider != "google":
        return Envelope(error_msg="provider not supported", status_code=status.HTTP_400_BAD_REQUEST)

    client_id_data = await users_service.get_google_client_id()
    return Envelope(
        data=ProviderClientIDResponse(
            client_id=client_id_data.client_id,
            state=client_id_data.state,
        )
    )


@router.post("/provider/{provider}/callback", response_model=Envelope[str])
async def provider_callback(
    provider: str,
    request: ProviderCallbackRequest,
    response: Response,
    users_service: Annotated[UserService, Depends(get_users_service)],
) -> Envelope[str]:
    if provider != "google":
        return Envelope(error_msg="provider not supported", status_code=status.HTTP_400_BAD_REQUEST)

    user = await users_service.google_callback(request)

    access_token = await create_access_token(data={"sub": user.email})
    refresh_token = await create_refresh_token(data={"sub": user.email})

    set_auth_cookies(response, access_token, refresh_token)

    return Envelope(data="ok")
