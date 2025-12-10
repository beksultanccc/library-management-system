from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class BorrowRequest(BaseModel):
    copy_id: int
    expected_days: int = 14


class BorrowResponse(BaseModel):
    transaction_id: int
    user_id: int
    copy_id: int
    borrow_date: datetime
    due_date: datetime
    fine_amount: float = 0.0

    class Config:
        from_attributes = True


class ReturnRequest(BaseModel):
    transaction_id: int
    returned_at: Optional[datetime] = None


class ReturnResponse(BaseModel):
    transaction_id: int
    return_date: datetime
    fine_amount: float = 0.0
    days_overdue: int = 0

    class Config:
        from_attributes = True


class TransactionResponse(BaseModel):
    transaction_id: int
    user_id: int
    copy_id: int
    type: str
    borrow_date: datetime
    due_date: datetime
    return_date: Optional[datetime] = None
    fine_amount: float = 0.0
    status: str
    book_title: str
    user_name: str

    class Config:
        from_attributes = True


class ReservationRequest(BaseModel):
    book_id: int


class ReservationResponse(BaseModel):
    reservation_id: int
    user_id: int
    book_id: int
    reserved_at: datetime
    expires_at: datetime
    status: str
    book_title: str

    class Config:
        from_attributes = True


class FineResponse(BaseModel):
    fine_id: int
    user_id: int
    transaction_id: int
    amount: float
    issued_at: datetime
    paid: bool
    paid_at: Optional[datetime] = None
    transaction_details: Optional[str] = None

    class Config:
        from_attributes = True