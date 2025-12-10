
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import json
import logging

from ..models.audit import (
    AuditLog, UserActivity, SecurityEvent, APIAccessLog,
    SystemLog, DataChangeLog, AuditAction, AuditEntity
)
from ..models.user import User
from ..schemas.audit import AuditFilter, AuditStats

logger = logging.getLogger(__name__)


class AuditService:

    @staticmethod
    async def log_action(
            db: Session,
            user_id: Optional[int],
            action: str,
            action_type: str,
            entity_type: Optional[str] = None,
            entity_id: Optional[int] = None,
            details: Optional[Dict[str, Any]] = None,
            ip_address: Optional[str] = None,
            user_agent: Optional[str] = None,
            status: str = "success",
            error_message: Optional[str] = None
    ) -> AuditLog:
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            action_type=action_type,
            ip_address=ip_address,
            user_agent=user_agent,
            details=json.dumps(details or {}),
            status=status,
            error_message=error_message
        )

        try:
            db.add(audit_log)
            db.commit()
            db.refresh(audit_log)

            logger.info(f"Аудит журналы қосылды: {action} by user {user_id}")

        except Exception as e:
            db.rollback()
            logger.error(f"Аудит журналын сақтау қатесі: {e}")
            raise

        return audit_log

    @staticmethod
    async def log_user_activity(
            db: Session,
            user_id: int,
            activity_type: str,
            details: Optional[Dict[str, Any]] = None,
            ip_address: Optional[str] = None,
            user_agent: Optional[str] = None
    ) -> UserActivity:

        user_activity = UserActivity(
            user_id=user_id,
            activity_type=activity_type,
            ip_address=ip_address,
            user_agent=user_agent,
            details=json.dumps(details or {})
        )

        try:
            db.add(user_activity)
            db.commit()
            db.refresh(user_activity)
        except Exception as e:
            db.rollback()
            logger.error(f"Пайдаланушы әрекетін сақтау қатесі: {e}")
            raise

        return user_activity

    @staticmethod
    async def log_security_event(
            db: Session,
            event_type: str,
            severity: str,
            details: Dict[str, Any],
            user_id: Optional[int] = None,
            ip_address: Optional[str] = None,
            user_agent: Optional[str] = None
    ) -> SecurityEvent:
        security_event = SecurityEvent(
            user_id=user_id,
            event_type=event_type,
            severity=severity,
            ip_address=ip_address,
            user_agent=user_agent,
            details=json.dumps(details)
        )

        try:
            db.add(security_event)
            db.commit()
            db.refresh(security_event)

            if severity in ["high", "critical"]:
                logger.warning(f"Критикалық қауіпсіздік оқиғасы: {event_type} - {details}")

        except Exception as e:
            db.rollback()
            logger.error(f"Қауіпсіздік оқиғасын сақтау қатесі: {e}")
            raise

        return security_event

    @staticmethod
    async def log_api_access(
            db: Session,
            user_id: Optional[int],
            endpoint: str,
            method: str,
            status_code: int,
            response_time_ms: int,
            ip_address: Optional[str] = None,
            user_agent: Optional[str] = None,
            request_params: Optional[str] = None,
            request_body: Optional[str] = None,
            response_body: Optional[str] = None
    ) -> APIAccessLog:

        if request_body and len(request_body) > 1000:
            request_body = request_body[:1000] + "... [TRUNCATED]"

        if response_body and len(response_body) > 1000:
            response_body = response_body[:1000] + "... [TRUNCATED]"

        api_log = APIAccessLog(
            user_id=user_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time_ms=response_time_ms,
            ip_address=ip_address,
            user_agent=user_agent,
            request_params=request_params,
            request_body=request_body,
            response_body=response_body
        )

        try:
            db.add(api_log)
            db.commit()
            db.refresh(api_log)
        except Exception as e:
            db.rollback()
            logger.error(f"API журналын сақтау қатесі: {e}")

        return api_log

    @staticmethod
    async def log_data_change(
            db: Session,
            user_id: Optional[int],
            table_name: str,
            record_id: int,
            change_type: str,
            old_values: Optional[Dict[str, Any]] = None,
            new_values: Optional[Dict[str, Any]] = None,
            changed_fields: Optional[List[str]] = None
    ) -> DataChangeLog:

        change_log = DataChangeLog(
            user_id=user_id,
            table_name=table_name,
            record_id=record_id,
            change_type=change_type,
            old_values=json.dumps(old_values) if old_values else None,
            new_values=json.dumps(new_values) if new_values else None,
            changed_fields=json.dumps(changed_fields) if changed_fields else None
        )

        try:
            db.add(change_log)
            db.commit()
            db.refresh(change_log)
        except Exception as e:
            db.rollback()
            logger.error(f"Мәліметтер өзгерісі журналын сақтау қатесі: {e}")
            raise

        return change_log

    @staticmethod
    async def get_audit_logs(
            db: Session,
            filter_params: AuditFilter,
            current_user_id: Optional[int] = None
    ) -> tuple[List[AuditLog], int]:


        query = db.query(AuditLog).join(User, AuditLog.user_id == User.user_id, isouter=True)

        if filter_params.user_id:
            query = query.filter(AuditLog.user_id == filter_params.user_id)

        if filter_params.action:
            query = query.filter(AuditLog.action == filter_params.action)

        if filter_params.entity_type:
            query = query.filter(AuditLog.entity_type == filter_params.entity_type)

        if filter_params.entity_id:
            query = query.filter(AuditLog.entity_id == filter_params.entity_id)

        if filter_params.action_type:
            query = query.filter(AuditLog.action_type == filter_params.action_type)

        if filter_params.status:
            query = query.filter(AuditLog.status == filter_params.status)

        if filter_params.date_from:
            query = query.filter(AuditLog.timestamp >= filter_params.date_from)

        if filter_params.date_to:
            query = query.filter(AuditLog.timestamp <= filter_params.date_to)


        total = query.count()


        offset = (filter_params.page - 1) * filter_params.per_page
        query = query.order_by(desc(AuditLog.timestamp))
        query = query.offset(offset).limit(filter_params.per_page)

        logs = query.all()

        for log in logs:
            if log.user:
                log.username = log.user.username

        return logs, total

    @staticmethod
    async def get_audit_statistics(db: Session, days: int = 30) -> AuditStats:


        start_date = datetime.utcnow() - timedelta(days=days)

        total_logs = db.query(func.count(AuditLog.log_id)).scalar()
        successful_actions = db.query(func.count(AuditLog.log_id)).filter(
            AuditLog.status == "success"
        ).scalar()
        failed_actions = db.query(func.count(AuditLog.log_id)).filter(
            AuditLog.status == "failed"
        ).scalar()

        unique_users = db.query(func.count(func.distinct(AuditLog.user_id))).scalar()

        most_active_user_subquery = db.query(
            AuditLog.user_id,
            func.count(AuditLog.log_id).label('log_count')
        ).group_by(AuditLog.user_id).order_by(desc('log_count')).limit(1).subquery()

        most_active_user = db.query(User.username).join(
            most_active_user_subquery, User.user_id == most_active_user_subquery.c.user_id
        ).first()

        most_common_action = db.query(
            AuditLog.action,
            func.count(AuditLog.log_id).label('action_count')
        ).group_by(AuditLog.action).order_by(desc('action_count')).first()

        logs_by_date_query = db.query(
            func.date(AuditLog.timestamp).label('log_date'),
            func.count(AuditLog.log_id).label('log_count')
        ).filter(AuditLog.timestamp >= start_date).group_by(
            func.date(AuditLog.timestamp)
        ).order_by(func.date(AuditLog.timestamp)).all()

        logs_by_date = {str(row.log_date): row.log_count for row in logs_by_date_query}

        logs_by_action_type_query = db.query(
            AuditLog.action_type,
            func.count(AuditLog.log_id).label('log_count')
        ).group_by(AuditLog.action_type).all()

        logs_by_action_type = {row.action_type: row.log_count for row in logs_by_action_type_query}

        logs_by_entity_type_query = db.query(
            AuditLog.entity_type,
            func.count(AuditLog.log_id).label('log_count')
        ).filter(AuditLog.entity_type.isnot(None)).group_by(AuditLog.entity_type).all()

        logs_by_entity_type = {row.entity_type: row.log_count for row in logs_by_entity_type_query}

        return AuditStats(
            total_logs=total_logs or 0,
            successful_actions=successful_actions or 0,
            failed_actions=failed_actions or 0,
            unique_users=unique_users or 0,
            most_active_user=most_active_user.username if most_active_user else None,
            most_common_action=most_common_action.action if most_common_action else None,
            logs_by_date=logs_by_date,
            logs_by_action_type=logs_by_action_type,
            logs_by_entity_type=logs_by_entity_type
        )

    @staticmethod
    async def cleanup_old_logs(db: Session, days_to_keep: int = 90) -> int:


        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        old_logs_count = db.query(func.count(AuditLog.log_id)).filter(
            AuditLog.timestamp < cutoff_date
        ).scalar()

        deleted_count = db.query(AuditLog).filter(
            AuditLog.timestamp < cutoff_date
        ).delete(synchronize_session=False)

        db.commit()

        logger.info(f"Аудит журналдары тазаланды: {deleted_count} жазба жойылды")

        return deleted_count