from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class EmailPayload(BaseModel):
    to: EmailStr
    cc: list[EmailStr] = []
    bcc: list[EmailStr] = []
    subject: str
    body: str


class NotificationPayload(BaseModel):
    email: EmailPayload | None = None


class NotificationCreate(BaseModel):
    caller: str
    user_id: int | None = None
    channel: str = "email"
    deduplication_id: str
    send_at: datetime | None = None
    payload: NotificationPayload
    metadata_: dict[str, Any] = Field(default_factory=dict, alias="metadata")
