from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import redis
import json

from ..models.notification import Notification
from ..models.user import User
from ..schemas.notification import NotificationResponse, NotificationCreate
from ..core.config import settings


class NotificationService:
    @staticmethod
    def send_notification(
            db: Session,
            user_id: int,
            notification_type: str,
            message: str,
            channel: str = "email"
    ) -> NotificationResponse:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise ValueError("Пайдаланушы табылмады")

        notification = Notification(
            user_id=user_id,
            type=notification_type,
            message=message,
            channel=channel,
            notification_data=json.dumps({"email": user.email, "phone": user.phone_number})
        )

        db.add(notification)
        db.commit()
        db.refresh(notification)

        if channel == "email" and user.email:
            NotificationService.send_email_notification.delay(
                user.email, message, f"Кітапхана жүйесі - {notification_type}"
            )
        elif channel == "sms" and user.phone_number:
            NotificationService.send_sms_notification.delay(user.phone_number, message)

        return NotificationResponse.from_orm(notification)

    @staticmethod
    async def get_user_notifications(
            db: Session,
            user_id: int,
            unread_only: bool = False
    ) -> List[NotificationResponse]:

        query = db.query(Notification).filter(Notification.user_id == user_id)

        if unread_only:
            query = query.filter(Notification.read == False)

        notifications = query.order_by(Notification.sent_at.desc()).all()

        return [NotificationResponse.from_orm(notification) for notification in notifications]

    @staticmethod
    async def mark_as_read(db: Session, notification_id: int, user_id: int) -> bool:
        notification = db.query(Notification).filter(
            Notification.notification_id == notification_id,
            Notification.user_id == user_id
        ).first()

        if not notification:
            return False

        notification.read = True
        db.commit()
        return True

    @staticmethod
    async def mark_all_as_read(db: Session, user_id: int):
        db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.read == False
        ).update({"read": True})
        db.commit()

    @staticmethod
    async def delete_notification(db: Session, notification_id: int, user_id: int) -> bool:
        notification = db.query(Notification).filter(
            Notification.notification_id == notification_id,
            Notification.user_id == user_id
        ).first()

        if not notification:
            return False

        db.delete(notification)
        db.commit()
        return True