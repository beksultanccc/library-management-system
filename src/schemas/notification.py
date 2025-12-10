from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class NotificationBase(BaseModel):
    user_id: int
    type: str
    message: str
    channel: str = "email"


class NotificationCreate(NotificationBase):
    pass


class NotificationResponse(NotificationBase):
    notification_id: int
    sent_at: datetime
    read: bool
    notification_data: Optional[str] = None

    class Config:
        from_attributes = True