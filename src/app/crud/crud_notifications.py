from fastcrud import FastCRUD

from ..models.notification import Notification

CRUDNotification = FastCRUD[Notification, Notification, Notification, Notification, Notification, Notification]
crud_notifications = CRUDNotification(Notification)
