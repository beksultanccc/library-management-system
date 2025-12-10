from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.core.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    notification_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    type = Column(String(50), nullable=False)  # overdue, reservation, system, announcement
    message = Column(Text, nullable=False)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    read = Column(Boolean, default=False)
    channel = Column(String(20), default="email")  # email, sms, push
    notification_data = Column(String(500), default="{}")  # metadata орнына notification_data

    user = relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<Notification {self.notification_id} - {self.type}>"