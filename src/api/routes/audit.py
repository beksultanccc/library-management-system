
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.core.database import get_db
from src.models.audit import AuditLog, UserActivity, SecurityEvent
from src.schemas.audit import (
    AuditLogResponse, UserActivityResponse, SecurityEventResponse,
    AuditFilter, AuditStats
)
from src.services.audit_service import AuditService
from src.api.dependencies import get_current_active_user, require_roles

router = APIRouter(prefix="/api/audit", tags=["Аудит"])

@router.get("/logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[int] = Query(None),
    action_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "librarian"]))
):

    from datetime import datetime
    from dateutil import parser

    date_from = None
    if start_date:
        try:
            date_from = parser.parse(start_date)
        except:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Қате басталу күні форматы"
            )

    date_to = None
    if end_date:
        try:
            date_to = parser.parse(end_date)
        except:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Қате аяқталу күні форматы"
            )

    filter_params = AuditFilter(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        action_type=action_type,
        start_date=date_from,
        end_date=date_to,
        status=status_filter,
        page=page,
        per_page=per_page
    )

    logs, total = await AuditService.get_audit_logs(db, filter_params)

    response_headers = {
        "X-Total-Count": str(total),
        "X-Page": str(page),
        "X-Per-Page": str(per_page),
        "X-Total-Pages": str((total + per_page - 1) // per_page)
    }

    return logs

@router.get("/logs/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "librarian"]))
):

    log = db.query(AuditLog).filter(AuditLog.log_id == log_id).first()
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Аудит журналы табылмады"
        )

    if log.user:
        log.username = log.user.username

    return log

@router.get("/user-activities", response_model=List[UserActivityResponse])
async def get_user_activities(
    user_id: Optional[int] = Query(None),
    activity_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "librarian"]))
):

    query = db.query(UserActivity).join(User)

    if user_id:
        query = query.filter(UserActivity.user_id == user_id)

    if activity_type:
        query = query.filter(UserActivity.activity_type == activity_type)

    from datetime import datetime
    from dateutil import parser

    if start_date:
        try:
            date_from = parser.parse(start_date)
            query = query.filter(UserActivity.activity_time >= date_from)
        except:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Қате басталу күні форматы"
            )

    if end_date:
        try:
            date_to = parser.parse(end_date)
            query = query.filter(UserActivity.activity_time <= date_to)
        except:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Қате аяқталу күні форматы"
            )

    total = query.count()

    offset = (page - 1) * per_page
    activities = query.order_by(UserActivity.activity_time.desc())\
                     .offset(offset)\
                     .limit(per_page)\
                     .all()

    for activity in activities:
        if activity.user:
            activity.username = activity.user.username

    response_headers = {
        "X-Total-Count": str(total),
        "X-Page": str(page),
        "X-Per-Page": str(per_page),
        "X-Total-Pages": str((total + per_page - 1) // per_page)
    }

    return activities

@router.get("/security-events", response_model=List[SecurityEventResponse])
async def get_security_events(
    resolved: Optional[bool] = Query(None),
    severity: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin"]))
):

    query = db.query(SecurityEvent).join(User, SecurityEvent.user_id == User.user_id, isouter=True)\
                                   .join(User, SecurityEvent.resolved_by == User.user_id, isouter=True)

    if resolved is not None:
        query = query.filter(SecurityEvent.resolved == resolved)

    if severity:
        query = query.filter(SecurityEvent.severity == severity)

    from datetime import datetime
    from dateutil import parser

    if start_date:
        try:
            date_from = parser.parse(start_date)
            query = query.filter(SecurityEvent.event_time >= date_from)
        except:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Қате басталу күні форматы"
            )

    if end_date:
        try:
            date_to = parser.parse(end_date)
            query = query.filter(SecurityEvent.event_time <= date_to)
        except:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Қате аяқталу күні форматы"
            )


    total = query.count()


    offset = (page - 1) * per_page
    events = query.order_by(SecurityEvent.event_time.desc())\
                  .offset(offset)\
                  .limit(per_page)\
                  .all()

    for event in events:
        if event.user:
            event.username = event.user.username
        if event.resolver:
            event.resolver_username = event.resolver.username
    response_headers = {
        "X-Total-Count": str(total),
        "X-Page": str(page),
        "X-Per-Page": str(per_page),
        "X-Total-Pages": str((total + per_page - 1) // per_page)
    }

    return events

@router.post("/security-events/{event_id}/resolve")
async def resolve_security_event(
    event_id: int,
    resolution_notes: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin"]))
):

    from datetime import datetime

    event = db.query(SecurityEvent).filter(SecurityEvent.event_id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Қауіпсіздік оқиғасы табылмады"
        )

    event.resolved = True
    event.resolved_at = datetime.utcnow()
    event.resolved_by = current_user.user_id
    event.resolution_notes = resolution_notes

    db.commit()

    return {"message": "Қауіпсіздік оқиғасы сәтті шешілді"}

@router.get("/statistics", response_model=AuditStats)
async def get_audit_statistics(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "librarian"]))
):
    stats = await AuditService.get_audit_statistics(db, days)
    return stats

@router.post("/cleanup")
async def cleanup_audit_logs(
    days_to_keep: int = 90,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin"]))
):

    if days_to_keep < 7:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Күндердің ең аз саны 7 болуы керек"
        )

    deleted_count = await AuditService.cleanup_old_logs(db, days_to_keep)

    return {
        "message": f"Аудит журналдары тазаланды",
        "deleted_records": deleted_count,
        "days_to_keep": days_to_keep
    }

@router.get("/dashboard")
async def get_audit_dashboard(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["admin", "librarian"]))
):
    from datetime import datetime, timedelta

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    total_logs = db.query(func.count(AuditLog.log_id)).filter(
        AuditLog.timestamp >= start_date
    ).scalar()

    actions_by_type = db.query(
        AuditLog.action_type,
        func.count(AuditLog.log_id).label('count')
    ).filter(
        AuditLog.timestamp >= start_date
    ).group_by(AuditLog.action_type).all()

    logs_by_status = db.query(
        AuditLog.status,
        func.count(AuditLog.log_id).label('count')
    ).filter(
        AuditLog.timestamp >= start_date
    ).group_by(AuditLog.status).all()

    recent_activities = db.query(UserActivity)\
                         .filter(UserActivity.activity_time >= start_date)\
                         .order_by(UserActivity.activity_time.desc())\
                         .limit(10)\
                         .all()

    recent_security_events = db.query(SecurityEvent)\
                              .filter(SecurityEvent.event_time >= start_date)\
                              .order_by(SecurityEvent.event_time.desc())\
                              .limit(10)\
                              .all()

    return {
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days": days
        },
        "total_logs": total_logs,
        "actions_by_type": {row.action_type: row.count for row in actions_by_type},
        "logs_by_status": {row.status: row.count for row in logs_by_status},
        "recent_activities": [
            {
                "activity_id": act.activity_id,
                "user_id": act.user_id,
                "activity_type": act.activity_type,
                "activity_time": act.activity_time.isoformat(),
                "username": act.user.username if act.user else None
            }
            for act in recent_activities
        ],
        "recent_security_events": [
            {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "severity": event.severity,
                "event_time": event.event_time.isoformat(),
                "resolved": event.resolved,
                "username": event.user.username if event.user else None
            }
            for event in recent_security_events
        ]
    }