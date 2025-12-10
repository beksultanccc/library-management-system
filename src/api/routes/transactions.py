from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from src.core.database import get_db
from src.schemas.transaction import (
    BorrowRequest, BorrowResponse, ReturnRequest, ReturnResponse,
    TransactionResponse, ReservationRequest, ReservationResponse,
    FineResponse
)
from src.services.transaction_service import TransactionService
from src.services.reservation_service import ReservationService
from src.api.dependencies import get_current_active_user, require_roles

router = APIRouter(prefix="/api/transactions", tags=["Транзакциялар"])

@router.post("/borrow", response_model=BorrowResponse)
async def borrow_book(
    request: BorrowRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["student", "teacher", "librarian", "admin"]))
):
    try:
        transaction = await TransactionService.borrow_book(
            db, current_user.user_id, request.copy_id, request.expected_days
        )
        return transaction
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/return", response_model=ReturnResponse)
async def return_book(
    request: ReturnRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["librarian", "admin"]))
):
    try:
        result = await TransactionService.return_book(
            db, request.transaction_id, request.returned_at
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{transaction_id}/renew")
async def renew_book(
    transaction_id: int,
    days: int = 7,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["student", "teacher", "librarian", "admin"]))
):
    try:
        transaction = await TransactionService.renew_book(
            db, transaction_id, current_user.user_id, days
        )
        return transaction
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/my-borrowings", response_model=List[TransactionResponse])
async def get_my_borrowings(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    transactions = await TransactionService.get_user_transactions(
        db, current_user.user_id, status_filter="active"
    )
    return transactions

@router.get("/overdue", response_model=List[TransactionResponse])
async def get_overdue_books(
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["librarian", "admin"]))
):
    transactions = await TransactionService.get_overdue_transactions(db)
    return transactions

@router.post("/reservations", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
async def create_reservation(
    request: ReservationRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    try:
        reservation = await ReservationService.create_reservation(
            db, current_user.user_id, request.book_id
        )
        return reservation
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/reservations/my", response_model=List[ReservationResponse])
async def get_my_reservations(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    reservations = await ReservationService.get_user_reservations(
        db, current_user.user_id
    )
    return reservations

@router.delete("/reservations/{reservation_id}")
async def cancel_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    success = await ReservationService.cancel_reservation(
        db, reservation_id, current_user.user_id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Резерв табылмады"
        )
    return {"message": "Резерв сәтті болдырылды"}

@router.get("/fines/my", response_model=List[FineResponse])
async def get_my_fines(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    fines = await TransactionService.get_user_fines(db, current_user.user_id)
    return fines

@router.post("/fines/{fine_id}/pay")
async def pay_fine(
    fine_id: int,
    amount: float,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    try:
        fine = await TransactionService.pay_fine(db, fine_id, current_user.user_id, amount)
        return fine
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/all", response_model=List[TransactionResponse])
async def get_all_transactions(
    user_id: int = None,
    status: str = None,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["librarian", "admin"]))
):
    transactions = await TransactionService.get_all_transactions(db, user_id, status)
    return transactions