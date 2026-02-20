import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from ...crud.crud_notifications import crud_notifications
from ...models.notification import NotificationStatus
from ...schemas.notification import EmailPayload, NotificationCreate, NotificationPayload
from .smtp import SMTPClient


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.smtp_client = SMTPClient()

    async def send_email(self, to: str, subject: str, body: str, caller: str = "system") -> None:
        """
        Send an email immediately.
        """
        payload = EmailPayload(
            to=to,
            subject=subject,
            body=body
        )
        
        # Create Notification record
        notification_in = NotificationCreate(
            caller=caller,
            deduplication_id=str(uuid.uuid4()),
            payload=NotificationPayload(email=payload),
            send_at=datetime.now(UTC)
        )
        
        # We save it as NEW first (or PENDING)
        notification_data = notification_in.model_dump()
        notification_data["status"] = NotificationStatus.PENDING.value
        
        # Using FastCRUD to create
        notification = await crud_notifications.create(db=self.db, object=notification_in, schema_to_select=crud_notifications.model, return_as_model=False)
        
        # Try to send
        try:
            await self.smtp_client.send(payload)
            # Update status to SENT
            await crud_notifications.update(
                db=self.db, 
                id=notification["id"], 
                object={"status": NotificationStatus.SENT.value, "updated_at": datetime.now(UTC)}
            )
        except Exception as e:
            # Update status to FAILED
            # In a real system, we might want to log the error to 'metadata' or a separate error log
            await crud_notifications.update(
                db=self.db, 
                id=notification["id"], 
                object={
                    "status": NotificationStatus.FAILED.value, 
                    "updated_at": datetime.now(UTC),
                    "metadata": {"error": str(e)}
                }
            )
            # Re-raise so caller knows it failed? 
            # Or suppress? Go code suppresses and marks as failed in background process usually,
            # but for synchronous 'send_email', we might want to know.
            # The current AuthService expects send_email to raise if it fails (so it can delete the OTP key).
            raise e
