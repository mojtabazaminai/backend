from datetime import UTC, datetime
from enum import Enum
from typing import Any

from sqlalchemy import DateTime, Integer, String, JSON
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db.database import Base


class NotificationStatus(str, Enum):
    NEW = "new"
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class NotificationChannel(str, Enum):
    EMAIL = "email"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, init=False)
    caller: Mapped[str] = mapped_column(String, nullable=False)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    deduplication_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    channel: Mapped[str] = mapped_column(String, nullable=False, default=NotificationChannel.EMAIL.value)
    status: Mapped[str] = mapped_column(String, nullable=False, default=NotificationStatus.NEW.value)
    send_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=True, default_factory=dict)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default_factory=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None,
        onupdate=lambda: datetime.now(UTC),
    )
