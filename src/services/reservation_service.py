
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional

from ..models.transaction import Reservation
from ..models.book import Book, BookCopy
from ..models.user import User
from ..schemas.transaction import ReservationRequest, ReservationResponse
from ..core.config import settings
from ..services.audit_service import AuditService


class ReservationService:
    @staticmethod
    async def create_reservation(db: Session, user_id: int, book_id: int) -> ReservationResponse:

        user = db.query(User).filter(User.user_id == user_id).first()
        if not user or not user.is_active:
            raise ValueError("Пайдаланушы белсенді емес немесе табылмады")

        book = db.query(Book).filter(Book.book_id == book_id).first()
        if not book:
            raise ValueError("Кітап табылмады")

        active_reservations = db.query(Reservation).filter(
            Reservation.user_id == user_id,
            Reservation.status == "active"
        ).count()

        if active_reservations >= 3:
            raise ValueError("Сізде қазірдің өзінде максималды санында резерв бар")

        available_copies = db.query(BookCopy).filter(
            BookCopy.book_id == book_id,
            BookCopy.status == "available"
        ).count()

        if available_copies > 0:
            raise ValueError("Кітап қазір қолжетімді, резерв қажет емес")

        reserved_at = datetime.utcnow()
        expires_at = reserved_at + timedelta(days=settings.RESERVATION_EXPIRE_DAYS)

        reservation = Reservation(
            user_id=user_id,
            book_id=book_id,
            reserved_at=reserved_at,
            expires_at=expires_at,
            status="active"
        )

        db.add(reservation)
        db.commit()
        db.refresh(reservation)

        return ReservationResponse(
            reservation_id=reservation.reservation_id,
            user_id=user_id,
            book_id=book_id,
            reserved_at=reserved_at,
            expires_at=expires_at,
            status="active",
            book_title=book.title
        )