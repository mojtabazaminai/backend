from typing import Any, Generic, TypeVar

from pydantic import BaseModel, EmailStr, Field

T = TypeVar("T")


class Envelope(BaseModel, Generic[T]):
    error_msg: str = ""
    error_metadata: dict[str, Any] | None = None
    data: T | None = None
    status_code: int = 200


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    user_id: int
    action: str


class OTPLoginRequest(BaseModel):
    email: EmailStr


class OTPVerifyRequest(BaseModel):
    email: EmailStr
    token: str


class OTPResponse(BaseModel):
    ttl: int
    length: int


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetVerifyRequest(BaseModel):
    email: EmailStr
    token: str
    password: str = Field(..., min_length=8)


class ProviderCallbackRequest(BaseModel):
    state: str
    code: str


ProviderCallback = ProviderCallbackRequest


class ProviderClientIDResponse(BaseModel):
    client_id: str
    state: str


ProviderClientID = ProviderClientIDResponse


class EmailRegisterRequest(BaseModel):
    email: EmailStr


class SubscriptionSummary(BaseModel):
    tier: str
    used: int
    remaining: int
    remaining_days: int
    limit_status: str
    renewal_status: str


class MeResponse(BaseModel):
    name: str
    avatar: str | None = None
    subscription: SubscriptionSummary | None = None


class ProfileUpdateRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    name: str | None = None
    avatar: str | None = None
    password: str | None = None
    previous_password: str | None = None


class GoogleUserInfo(BaseModel):
    id: str
    email: EmailStr
    verified_email: bool
    name: str
    given_name: str | None = None
    family_name: str | None = None
    picture: str | None = None