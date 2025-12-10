from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from src.core.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    copy_id = Column(Integer, ForeignKey("book_copies.copy_id"), nullable=False)
    type = Column(String(20), nullable=False)  # borrow, return, renew
    borrow_date = Column(DateTime(timezone=True), server_default=func.now())
    due_date = Column(DateTime(timezone=True), nullable=False)
    return_date = Column(DateTime(timezone=True), nullable=True)
    fine_amount = Column(Numeric(10, 2), default=0.0)
    status = Column(String(20), default="active")  # active, returned, overdue, cancelled

    user = relationship("User", back_populates="transactions")
    book_copy = relationship("BookCopy", back_populates="transactions")
    fine = relationship("Fine", back_populates="transaction", uselist=False)

    def __repr__(self):
        return f"<Transaction {self.transaction_id} - {self.type}>"


class Reservation(Base):
    __tablename__ = "reservations"

    reservation_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.book_id"), nullable=False)
    reserved_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(20), default="active")  # active, fulfilled, cancelled, expired

    user = relationship("User", back_populates="reservations")
    book = relationship("Book", back_populates="reservations")

    def __repr__(self):
        return f"<Reservation {self.reservation_id}>"


class Fine(Base):
    __tablename__ = "fines"

    fine_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    transaction_id = Column(Integer, ForeignKey("transactions.transaction_id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    issued_at = Column(DateTime(timezone=True), server_default=func.now())
    paid = Column(Boolean, default=False)
    paid_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="fines")
    transaction = relationship("Transaction", back_populates="fine")

    def __repr__(self):
        return f"<Fine {self.fine_id} - {self.amount}>"