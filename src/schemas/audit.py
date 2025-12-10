
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class AuditLogBase(BaseModel):

    user_id: Optional[int] = None
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    action_type: str
    details: Optional[Dict[str, Any]] = {}
    status: str = "success"
    error_message: Optional[str] = None


class AuditLogCreate(AuditLogBase):

    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class AuditLogResponse(AuditLogBase):

    log_id: int
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    username: Optional[str] = None

    class Config:
        from_attributes = True


class UserActivityBase(BaseModel):

    user_id: int
    activity_type: str
    details: Optional[Dict[str, Any]] = {}


class UserActivityCreate(UserActivityBase):

    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class UserActivityResponse(UserActivityBase):

    activity_id: int
    activity_time: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    username: str

    class Config:
        from_attributes = True


class SecurityEventBase(BaseModel):
    user_id: Optional[int] = None
    event_type: str
    severity: str
    details: Dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class SecurityEventCreate(SecurityEventBase):
    pass


class SecurityEventResponse(SecurityEventBase):

    event_id: int
    event_time: datetime
    action_taken: Optional[str] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[int] = None
    resolution_notes: Optional[str] = None
    username: Optional[str] = None
    resolver_username: Optional[str] = None

    class Config:
        from_attributes = True


class AuditFilter(BaseModel):
    user_id: Optional[int] = None
    action: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    action_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None
    page: int = Field(1, ge=1)
    per_page: int = Field(50, ge=1, le=100)


class AuditStats(BaseModel):
    total_logs: int
    successful_actions: int
    failed_actions: int
    unique_users: int
    most_active_user: Optional[str] = None
    most_common_action: Optional[str] = None
    logs_by_date: Dict[str, int]
    logs_by_action_type: Dict[str, int]
    logs_by_entity_type: Dict[str, int]