from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
from typing import List, Optional
import redis

from ..models.transaction import Transaction, Fine
from ..models.book import Book, BookCopy
from ..models.user import User
from ..schemas.transaction import BorrowResponse, ReturnResponse, TransactionResponse, FineResponse
from ..core.config import settings
from ..services.audit_service import AuditService
from ..services.notification_service import NotificationService


class TransactionService:
    @staticmethod
    async def borrow_book(db: Session, user_id: int, copy_id: int, expected_days: int = 14) -> BorrowResponse:

        user = db.query(User).filter(User.user_id == user_id).first()
        if not user or not user.is_active:
            raise ValueError("Пайдаланушы белсенді емес немесе табылмады")

        book_copy = db.query(BookCopy).filter(BookCopy.copy_id == copy_id).first()
        if not book_copy:
            raise ValueError("Кітап көшірмесі табылмады")

        if book_copy.status != "available":
            raise ValueError("Кітап қолжетімді емес")

        active_borrowings = db.query(Transaction).filter(
            and_(
                Transaction.user_id == user_id,
                Transaction.status == "active"
            )
        ).count()

        if active_borrowings >= 5:
            raise ValueError("Сізде қазірдің өзінде максималды санында кітап бар")

        unpaid_fines = db.query(Fine).filter(
            and_(
                Fine.user_id == user_id,
                Fine.paid == False
            )
        ).all()

        if unpaid_fines:
            total_unpaid = sum([fine.amount for fine in unpaid_fines])
            if total_unpaid > 1000:  # Егер 1000 теңгеден асса
                raise ValueError(f"Сізде төленбеген айыппұл бар: {total_unpaid} теңге")

        if expected_days < 1 or expected_days > settings.MAX_BORROW_DAYS:
            raise ValueError(f"Қарыз мерзімі 1-ден {settings.MAX_BORROW_DAYS} күнге дейін болуы керек")

        borrow_date = datetime.utcnow()
        due_date = borrow_date + timedelta(days=expected_days)

        transaction = Transaction(
            user_id=user_id,
            copy_id=copy_id,
            type="borrow",
            borrow_date=borrow_date,
            due_date=due_date,
            status="active"
        )

        book_copy.status = "borrowed"

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        redis_client = redis.Redis.from_url(settings.REDIS_URL)
        redis_client.delete(f"user:{user_id}:transactions")

        await AuditService.log_action(
            db,
            user_id=user_id,
            action="book_borrowed",
            action_type="create",
            entity_type="transaction",
            entity_id=transaction.transaction_id,
            details={
                "transaction_id": transaction.transaction_id,
                "copy_id": copy_id,
                "expected_days": expected_days
            }
        )

        book = db.query(Book).filter(Book.book_id == book_copy.book_id).first()
        if book:
            message = f"Сіз '{book.title}' кітабын {due_date.strftime('%Y-%m-%d')} мерзіміне дейін қарызға алдыңыз."
            NotificationService.send_notification_async.delay(
                user_id, "borrow", message, "email"
            )

        return BorrowResponse(
            transaction_id=transaction.transaction_id,
            user_id=user_id,
            copy_id=copy_id,
            borrow_date=borrow_date,
            due_date=due_date,
            fine_amount=0.0
        )

    @staticmethod
    async def return_book(db: Session, transaction_id: int, returned_at: Optional[datetime] = None) -> ReturnResponse:
        transaction = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
        if not transaction:
            raise ValueError("Транзакция табылмады")

        if transaction.status != "active":
            raise ValueError("Бұл транзакция белсенді емес")

        return_date = returned_at or datetime.utcnow()

        days_overdue = 0
        fine_amount = 0.0

        if return_date > transaction.due_date:
            days_overdue = (return_date - transaction.due_date).days
            fine_amount = min(days_overdue * settings.FINE_PER_DAY, settings.MAX_FINE_AMOUNT)

            if fine_amount > 0:
                fine = Fine(
                    user_id=transaction.user_id,
                    transaction_id=transaction_id,
                    amount=fine_amount,
                    paid=False
                )
                db.add(fine)

        transaction.return_date = return_date
        transaction.fine_amount = fine_amount
        transaction.status = "returned"

        book_copy = db.query(BookCopy).filter(BookCopy.copy_id == transaction.copy_id).first()
        if book_copy:
            book_copy.status = "available"

        db.commit()
        redis_client = redis.Redis.from_url(settings.REDIS_URL)
        redis_client.delete(f"user:{transaction.user_id}:transactions")

        await AuditService.log_action(
            db,
            user_id=transaction.user_id,
            action="book_returned",
            action_type="update",
            entity_type="transaction",
            entity_id=transaction_id,
            details={
                "transaction_id": transaction_id,
                "days_overdue": days_overdue,
                "fine_amount": fine_amount
            }
        )

        if days_overdue > 0:
            message = f"Сіз кітапты {days_overdue} күн мерзімі өтіп қайтардыңыз. Айыппұл: {fine_amount} теңге."
            NotificationService.send_notification_async.delay(
                transaction.user_id, "fine", message, "email"
            )

        return ReturnResponse(
            transaction_id=transaction_id,
            return_date=return_date,
            fine_amount=fine_amount,
            days_overdue=days_overdue
        )

    @staticmethod
    async def get_user_transactions(db: Session, user_id: int, status_filter: Optional[str] = None) -> List[
        TransactionResponse]:
        query = db.query(Transaction).filter(Transaction.user_id == user_id)

        if status_filter:
            query = query.filter(Transaction.status == status_filter)

        transactions = query.order_by(Transaction.borrow_date.desc()).all()

        result = []
        for transaction in transactions:
            book_copy = db.query(BookCopy).filter(BookCopy.copy_id == transaction.copy_id).first()
            book_title = ""
            if book_copy and book_copy.book:
                book_title = book_copy.book.title

            user = db.query(User).filter(User.user_id == user_id).first()
            user_name = user.full_name if user else ""

            result.append(TransactionResponse(
                transaction_id=transaction.transaction_id,
                user_id=user_id,
                copy_id=transaction.copy_id,
                type=transaction.type,
                borrow_date=transaction.borrow_date,
                due_date=transaction.due_date,
                return_date=transaction.return_date,
                fine_amount=float(transaction.fine_amount),
                status=transaction.status,
                book_title=book_title,
                user_name=user_name
            ))

        return result

    @staticmethod
    async def get_overdue_transactions(db: Session) -> List[TransactionResponse]:
        now = datetime.utcnow()

        transactions = db.query(Transaction).filter(
            and_(
                Transaction.status == "active",
                Transaction.due_date < now
            )
        ).all()

        result = []
        for transaction in transactions:
            book_copy = db.query(BookCopy).filter(BookCopy.copy_id == transaction.copy_id).first()
            book_title = ""
            if book_copy and book_copy.book:
                book_title = book_copy.book.title

            user = db.query(User).filter(User.user_id == transaction.user_id).first()
            user_name = user.full_name if user else ""

            result.append(TransactionResponse(
                transaction_id=transaction.transaction_id,
                user_id=transaction.user_id,
                copy_id=transaction.copy_id,
                type=transaction.type,
                borrow_date=transaction.borrow_date,
                due_date=transaction.due_date,
                return_date=transaction.return_date,
                fine_amount=float(transaction.fine_amount),
                status=transaction.status,
                book_title=book_title,
                user_name=user_name
            ))

        return result

    @staticmethod
    async def get_user_fines(db: Session, user_id: int) -> List[FineResponse]:
        fines = db.query(Fine).filter(Fine.user_id == user_id).all()

        result = []
        for fine in fines:
            transaction_details = ""
            transaction = db.query(Transaction).filter(Transaction.transaction_id == fine.transaction_id).first()
            if transaction:
                book_copy = db.query(BookCopy).filter(BookCopy.copy_id == transaction.copy_id).first()
                if book_copy and book_copy.book:
                    transaction_details = f"Кітап: {book_copy.book.title}"

            result.append(FineResponse(
                fine_id=fine.fine_id,
                user_id=fine.user_id,
                transaction_id=fine.transaction_id,
                amount=float(fine.amount),
                issued_at=fine.issued_at,
                paid=fine.paid,
                paid_at=fine.paid_at,
                transaction_details=transaction_details
            ))

        return result

    @staticmethod
    async def pay_fine(db: Session, fine_id: int, user_id: int, amount: float) -> FineResponse:
        fine = db.query(Fine).filter(Fine.fine_id == fine_id, Fine.user_id == user_id).first()
        if not fine:
            raise ValueError("Айыппұл табылмады")

        if fine.paid:
            raise ValueError("Айыппұл төленген")

        if amount < fine.amount:
            raise ValueError(f"Төлем сомасы жеткіліксіз. Толық сома: {fine.amount}")

        fine.paid = True
        fine.paid_at = datetime.utcnow()

        db.commit()

        await AuditService.log_action(
            db,
            user_id=user_id,
            action="fine_paid",
            action_type="update",
            entity_type="fine",
            entity_id=fine_id,
            details={
                "fine_id": fine_id,
                "amount": float(amount),
                "paid_amount": float(fine.amount)
            }
        )

        return FineResponse(
            fine_id=fine.fine_id,
            user_id=fine.user_id,
            transaction_id=fine.transaction_id,
            amount=float(fine.amount),
            issued_at=fine.issued_at,
            paid=fine.paid,
            paid_at=fine.paid_at,
            transaction_details=""
        )