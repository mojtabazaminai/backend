from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import update

from app.core.db.database import local_session
from app.models.notification import Notification, NotificationStatus


def _now(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(UTC)
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


async def promote_pending_notifications(now: datetime | None = None) -> dict[str, int]:
    timestamp = _now(now)
    async with local_session() as db:
        stmt = (
            update(Notification)
            .where(
                Notification.status == NotificationStatus.NEW.value,
                Notification.send_at.is_not(None),
                Notification.send_at < timestamp,
            )
            .values(status=NotificationStatus.PENDING.value, updated_at=timestamp)
        )
        result = await db.execute(stmt)
        await db.commit()

    updated = result.rowcount or 0
    return {"updated": updated}
