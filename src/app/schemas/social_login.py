from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class SocialLoginBase(BaseModel):
    provider_user_id: Annotated[str, Field(min_length=1, examples=["1234567890"])]
    provider: Annotated[str, Field(min_length=1, examples=["google"])]

    email: Annotated[str, Field(min_length=1, examples=["user.userson@example.com"])]
    name: Annotated[str, Field(min_length=1, examples=["User Userson"])]

    given_name: Annotated[str | None, Field(default=None, examples=["User"])]
    family_name: Annotated[str | None, Field(default=None, examples=["Userson"])]
    avatar_url: Annotated[
        str | None,
        Field(
            default=None,
            pattern=r"^(https?|ftp)://[^\s/$.?#].[^\s]*$",
            examples=["https://www.avatarurl.com/avatar.png"],
        ),
    ]


class SocialLoginCreate(SocialLoginBase):
    model_config = ConfigDict(extra="forbid")

    user_id: int


class SocialLoginUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider_user_id: Annotated[str | None, Field(default=None, examples=["0987654321"])]
    provider: Annotated[str | None, Field(default=None, examples=["github"])]

    email: Annotated[str | None, Field(default=None, examples=["updated@example.com"])]
    name: Annotated[str | None, Field(default=None, examples=["Updated Name"])]

    given_name: Annotated[str | None, Field(default=None, examples=["Updated"])]
    family_name: Annotated[str | None, Field(default=None, examples=["User"])]
    avatar_url: Annotated[
        str | None,
        Field(
            default=None,
            pattern=r"^(https?|ftp)://[^\s/$.?#].[^\s]*$",
            examples=["https://www.avatarurl.com/avatar.png"],
        ),
    ]
    user_id: int | None = None


class SocialLoginRead(BaseModel):
    id: int
    provider_user_id: str
    provider: str
    email: str
    name: str
    given_name: str | None
    family_name: str | None
    avatar_url: str | None
    user_id: int
    created_at: datetime
    updated_at: datetime | None
