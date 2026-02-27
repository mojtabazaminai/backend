import json
import uuid
from datetime import datetime, UTC
from enum import Enum
from typing import Any

from fastapi import HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.security import get_password_hash, verify_password
from ...crud.crud_users import crud_users
from ...schemas.auth import (
    EmailRegisterRequest,
    LoginRequest,
    OTPLoginRequest,
    OTPResponse,
    OTPVerifyRequest,
    PasswordResetRequest,
    PasswordResetVerifyRequest,
    ProviderCallback,
    ProviderClientID,
)
from ...models.subscription import SubscriptionPlan, UserSubscription
from ...schemas.user import UserCreateInternal, UserUpdate, UserRead
from ..notification.service import NotificationService
from .providers import GoogleProvider
from .utils import generate_secure_otp

OTP_LENGTH = 6
OTP_TTL = 600  # 10 minutes
OTP_RETRY_COUNT = 5
STATE_TTL = 300  # 5 minutes


class OTPReason(str, Enum):
    REGISTER = "email_register"
    LOGIN = "otp_login"
    PASSWORD_RESET = "password_reset"


class LoginAction(str, Enum):
    LOGIN = "login"
    REGISTER = "register"


class UserService:
    def __init__(self, db: AsyncSession, redis: Redis):
        self.db = db
        self.redis = redis
        self.notification_service = NotificationService(db)
        self.google_provider = GoogleProvider()

    async def _assign_trial_subscription(self, user_id: int) -> None:
        result = await self.db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.tier == "trial")
        )
        plan = result.scalars().first()
        if not plan:
            return
        subscription = UserSubscription(user_id=user_id, plan_id=plan.id, ended_at=None, canceled_at=None)
        self.db.add(subscription)
        await self.db.commit()

    def _get_otp_key(self, reason: OTPReason, email: str) -> str:
        return f"auth:otp:{reason.value}:{email}"

    async def _send_otp(self, email: str, reason: OTPReason) -> OTPResponse:
        key = self._get_otp_key(reason, email)
        
        # Check if OTP already exists
        existing_ttl = await self.redis.ttl(key)
        if existing_ttl > 0:
             # If exists, return the existing TTL (Go behavior: "otp already sent")
             return OTPResponse(ttl=existing_ttl, length=OTP_LENGTH)

        otp_code = generate_secure_otp(OTP_LENGTH)
        
        # Store in Redis with NX (only if not exists)
        data = {
            "code": otp_code,
            "retry_count": 0,
            "created_at": datetime.now(UTC).isoformat(),
        }
        
        is_set = await self.redis.set(key, json.dumps(data), ex=OTP_TTL, nx=True)
        
        if not is_set:
             # Race condition loser
             existing_ttl = await self.redis.ttl(key)
             return OTPResponse(ttl=existing_ttl, length=OTP_LENGTH)
        
        # Send Email
        try:
            await self.notification_service.send_email(
                to=email,
                subject=f"Your OTP Code for {reason.value}",
                body=f"Your OTP code is: {otp_code}"
            )
        except Exception as e:
            # If email fails, delete the key so user can try again
            await self.redis.delete(key)
            raise e
            
        return OTPResponse(ttl=OTP_TTL, length=OTP_LENGTH)

    async def _validate_otp(self, email: str, token: str, reason: OTPReason) -> None:
        key = self._get_otp_key(reason, email)
        data_json = await self.redis.get(key)
        
        if not data_json:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP invalid or expired"
            )
            
        data = json.loads(data_json)
        
        if data["retry_count"] >= OTP_RETRY_COUNT:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="OTP retry limit exceeded"
            )
            
        if data["code"] != token:
            data["retry_count"] += 1
            # Update retry count, keep original TTL
            ttl = await self.redis.ttl(key)
            if ttl > 0:
                await self.redis.set(key, json.dumps(data), ex=ttl)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP invalid"
            )
            
        # Success - delete key
        await self.redis.delete(key)

    async def email_login(self, req: LoginRequest):
        user = await crud_users.get(db=self.db, email=req.email, return_as_model=True, schema_to_select=UserRead)
        if not user or not user.password_hash:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
            
        if not await verify_password(req.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
            
        return user

    async def email_register_init(self, req: EmailRegisterRequest) -> OTPResponse:
        user = await crud_users.get(db=self.db, email=req.email, return_as_model=True, schema_to_select=UserRead)
        if user:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
        return await self._send_otp(req.email, OTPReason.REGISTER)

    async def email_otp_login_init(self, req: OTPLoginRequest) -> OTPResponse:
        reason = OTPReason.LOGIN
        user = await crud_users.get(db=self.db, email=req.email, return_as_model=True, schema_to_select=UserRead)
        if not user:
            # If user not found, treat as registration (Go behavior)
            reason = OTPReason.REGISTER
            
        return await self._send_otp(req.email, reason)

    async def email_otp_login_verify(self, req: OTPVerifyRequest) -> tuple[Any, LoginAction]:
        # Determine reason based on user existence
        user = await crud_users.get(db=self.db, email=req.email, return_as_model=True, schema_to_select=UserRead)
        reason = OTPReason.LOGIN if user else OTPReason.REGISTER
        
        await self._validate_otp(req.email, req.token, reason)
        
        if reason == OTPReason.LOGIN:
            return user, LoginAction.LOGIN
        else:
            # Register new user
            name = req.email.split("@")[0]
            user_in = UserCreateInternal(
                email=req.email,
                name=name,
                password_hash="" # No password for OTP users initially # No password for OTP users initially
            )
            new_user = await crud_users.create(db=self.db, object=user_in, schema_to_select=UserRead, return_as_model=True)
            await self._assign_trial_subscription(new_user.id)
            return new_user, LoginAction.REGISTER

    async def password_reset_init(self, req: PasswordResetRequest) -> OTPResponse:
        user = await crud_users.get(db=self.db, email=req.email, return_as_model=True, schema_to_select=UserRead)
        if not user:
             # To avoid user enumeration, we might want to fake success, 
             # but Go code returns error if user not found (implicitly via GetUserByEmail).
             # "GetUserByEmail" in Go usually returns error if not found.
             # I'll follow Go's lead and return error or check.
             # Go: _, err := s.repository.GetUserByEmail... if err != nil return err.
             raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        return await self._send_otp(req.email, OTPReason.PASSWORD_RESET)

    async def password_reset_verify(self, req: PasswordResetVerifyRequest):
        await self._validate_otp(req.email, req.token, OTPReason.PASSWORD_RESET)
        
        user = await crud_users.get(db=self.db, email=req.email, return_as_model=True, schema_to_select=UserRead)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        hashed_password = get_password_hash(req.password)
        user_update = UserUpdate(password_hash=hashed_password)
        return await crud_users.update(db=self.db, id=user.id, object=user_update, return_as_model=True, schema_to_select=UserRead)

    async def update_profile(self, user_id: int, req: UserUpdate, previous_password: str | None = None):
        # Handle password update specifically if included
        # Note: req is UserUpdate, which has password_hash field. 
        # If the caller is passing a raw password in a custom field, we need to handle it.
        # Go code: UpdateProfileRequest has Password *string.
        
        # Here we assume req.password_hash contains the NEW password (raw) if we want to change it?
        # Or we should have a specific request object.
        # The UserUpdate schema has password_hash.
        
        # If we follow the Go logic:
        # If req.Password != nil:
        #   check previous_password
        #   gen hash
        
        # Since I'm using `UserUpdate` which maps to Pydantic, I'll assume the caller handles logic or I do it here.
        # But `UserUpdate` in `schemas/user.py` has `password_hash`.
        # I'll stick to the Go logic: check previous password if updating password.
        
        user = await crud_users.get(db=self.db, id=user_id, return_as_model=True, schema_to_select=UserRead)
        if not user:
             raise HTTPException(status_code=404, detail="User not found")
             
        update_data = req.model_dump(exclude_unset=True)
        
        if "password_hash" in update_data and update_data["password_hash"]:
            # If trying to update password
            new_password_raw = update_data["password_hash"]
            
            if not previous_password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="previous_password is required to set new password"
                )
            
            if not user.password_hash or not await verify_password(previous_password, user.password_hash):
                 raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid previous password"
                )
                
            update_data["password_hash"] = get_password_hash(new_password_raw)
            
        return await crud_users.update(db=self.db, id=user.id, object=UserUpdate(**update_data), return_as_model=True, schema_to_select=UserRead)

    async def get_google_client_id(self) -> ProviderClientID:
        state = str(uuid.uuid4())
        await self.redis.set(f"auth:state:{state}", "google", ex=STATE_TTL)
        return ProviderClientID(client_id=self.google_provider.client_id, state=state)

    async def google_callback(self, req: ProviderCallback):
        # Validate state
        state_key = f"auth:state:{req.state}"
        provider_name = await self.redis.get(state_key)
        
        if not provider_name or provider_name.decode() != "google":
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired state"
            )
            
        # Delete state
        await self.redis.delete(state_key)
        
        # Get user data from Google
        google_user = await self.google_provider.get_user_data(req.code)
        
        # Find or create user
        user = await crud_users.get(db=self.db, email=google_user.email, return_as_model=True, schema_to_select=UserRead)
        if not user:
            # Create user
            user_in = UserCreateInternal(
                email=google_user.email,
                name=google_user.name,
                first_name=google_user.given_name,
                last_name=google_user.family_name,
                avatar_url=google_user.picture,
                password_hash="" # No password for OTP users initially # No password for OAuth users
            )
            user = await crud_users.create(db=self.db, object=user_in, schema_to_select=UserRead, return_as_model=True)
            await self._assign_trial_subscription(user.id)
        else:
            # Update user info if needed? Go code just returns user.
            # Go code: CreateFromProviderData -> likely upserts or just creates if not exists.
            # I will just return the user.
            pass
            
        return user
