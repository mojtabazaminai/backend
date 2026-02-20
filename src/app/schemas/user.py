from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    name: Annotated[str, Field(min_length=1, examples=["User Userson"])]
    first_name: Annotated[str | None, Field(default=None, examples=["User"])]
    last_name: Annotated[str | None, Field(default=None, examples=["Userson"])]
    email: Annotated[EmailStr, Field(examples=["user.userson@example.com"])]


class UserCreate(UserBase):
    model_config = ConfigDict(extra="forbid")

    # matches model column name: password_hash (we're not inventing "password")
    password_hash: Annotated[str | None, Field(default=None, examples=["$2b$12$..."])]
    avatar_url: Annotated[
        str | None,
        Field(
            default=None,
            pattern=r"^(https?|ftp)://[^\s/$.?#].[^\s]*$",
            examples=["https://www.avatarurl.com/avatar.png"],
        ),
    ]

class UserCreateInternal(UserBase):
    password_hash: str
class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Annotated[str | None, Field(min_length=1, default=None, examples=["Updated Name"])]
    first_name: Annotated[str | None, Field(default=None, examples=["Updated"])]
    last_name: Annotated[str | None, Field(default=None, examples=["User"])]
    email: Annotated[EmailStr | None, Field(default=None, examples=["updated@example.com"])]
    password_hash: Annotated[str | None, Field(default=None, examples=["$2b$12$..."])]
    avatar_url: Annotated[
        str | None,
        Field(
            default=None,
            pattern=r"^(https?|ftp)://[^\s/$.?#].[^\s]*$",
            examples=["https://www.avatarurl.com/avatar.png"],
        ),
    ]

class UserUpdateInternal(UserUpdate):
    updated_at: datetime


class UserRead(BaseModel):
    id: int
    name: str
    first_name: str | None
    last_name: str | None
    email: EmailStr
    password_hash: str | None
    avatar_url: str | None
    created_at: datetime
    updated_at: datetime | None

class UserDelete(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_deleted: bool
    deleted_at: datetime

