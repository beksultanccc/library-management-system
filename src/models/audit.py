
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean  # Boolean қосу!
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from src.core.database import Base


class AuditLog(Base):

    __tablename__ = "audit_logs"

    log_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(Integer, nullable=True)
    action_type = Column(String(20), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    details = Column(Text, default="{}")
    status = Column(String(20), default="success")
    error_message = Column(Text, nullable=True)

    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        return f"<AuditLog {self.log_id} - {self.action} by {self.user_id}>"

    def to_dict(self):

        return {
            "log_id": self.log_id,
            "user_id": self.user_id,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "action_type": self.action_type,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "details": self.details,
            "status": self.status,
            "error_message": self.error_message
        }


class SystemLog(Base):

    __tablename__ = "system_logs"

    log_id = Column(Integer, primary_key=True, index=True)
    level = Column(String(20), nullable=False)
    logger = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    module = Column(String(100), nullable=True)
    function = Column(String(100), nullable=True)
    line_number = Column(Integer, nullable=True)
    exception_info = Column(Text, nullable=True)
    request_id = Column(String(100), nullable=True)

    def __repr__(self):
        return f"<SystemLog {self.log_id} - {self.level}: {self.message[:50]}...>"


class UserActivity(Base):

    __tablename__ = "user_activities"

    activity_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    activity_type = Column(String(50), nullable=False)  # login, logout, profile_update, password_change
    activity_time = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    details = Column(Text, default="{}")

    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        return f"<UserActivity {self.activity_id} - {self.user_id}: {self.activity_type}>"


class APIAccessLog(Base):

    __tablename__ = "api_access_logs"

    log_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    endpoint = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer, nullable=False)
    request_time = Column(DateTime(timezone=True), server_default=func.now())
    response_time_ms = Column(Integer, nullable=False)
    user_agent = Column(String(500), nullable=True)
    request_params = Column(Text, nullable=True)
    request_body = Column(Text, nullable=True)
    response_body = Column(Text, nullable=True)

    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        return f"<APIAccessLog {self.log_id} - {self.method} {self.endpoint}: {self.status_code}>"


class SecurityEvent(Base):

    __tablename__ = "security_events"

    event_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    event_type = Column(String(50), nullable=False)  # failed_login, password_guess, suspicious_activity
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    event_time = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    details = Column(Text, nullable=False)
    action_taken = Column(String(100), nullable=True)  # block_ip, lock_account, notify_admin
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    user = relationship("User", foreign_keys=[user_id], primaryjoin="SecurityEvent.user_id == User.user_id")
    resolver = relationship("User", foreign_keys=[resolved_by], primaryjoin="SecurityEvent.resolved_by == User.user_id")

    def __repr__(self):
        return f"<SecurityEvent {self.event_id} - {self.event_type} ({self.severity})>"


class DataChangeLog(Base):

    __tablename__ = "data_change_logs"

    change_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    table_name = Column(String(100), nullable=False)
    record_id = Column(Integer, nullable=False)
    change_type = Column(String(10), nullable=False)
    change_time = Column(DateTime(timezone=True), server_default=func.now())
    old_values = Column(Text, nullable=True)
    new_values = Column(Text, nullable=True)
    changed_fields = Column(Text, nullable=True)

    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        return f"<DataChangeLog {self.change_id} - {self.table_name}.{self.record_id}: {self.change_type}>"


class AuditAction:

    LOGIN = "user_login"
    LOGOUT = "user_logout"
    REGISTER = "user_register"
    PROFILE_UPDATE = "profile_update"
    PASSWORD_CHANGE = "password_change"

    BOOK_CREATE = "book_create"
    BOOK_UPDATE = "book_update"
    BOOK_DELETE = "book_delete"

    TRANSACTION_CREATE = "transaction_create"
    TRANSACTION_UPDATE = "transaction_update"
    TRANSACTION_DELETE = "transaction_delete"

    RESERVATION_CREATE = "reservation_create"
    RESERVATION_CANCEL = "reservation_cancel"

    FINE_CREATE = "fine_create"
    FINE_PAY = "fine_pay"

    SYSTEM_CONFIG_UPDATE = "system_config_update"


class AuditEntity:

    USER = "user"
    ROLE = "role"
    BOOK = "book"
    AUTHOR = "author"
    CATEGORY = "category"
    BOOK_COPY = "book_copy"
    TRANSACTION = "transaction"
    RESERVATION = "reservation"
    FINE = "fine"
    NOTIFICATION = "notification"
    SYSTEM = "system"


from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class AuditLogSchema(BaseModel):

    log_id: Optional[int] = None
    user_id: Optional[int] = None
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    action_type: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[Dict[str, Any]] = {}
    status: str = "success"
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    log_id: int
    user_id: Optional[int]
    action: str
    entity_type: Optional[str]
    entity_id: Optional[int]
    action_type: str
    timestamp: datetime
    ip_address: Optional[str]
    user_agent: Optional[str]
    details: str
    status: str
    error_message: Optional[str]
    username: Optional[str]

    class Config:
        from_attributes = True


class AuditFilter(BaseModel):
    user_id: Optional[int] = None
    action: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    action_type: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    status: Optional[str] = None
    page: int = 1
    per_page: int = 50

    class Config:
        from_attributes = True