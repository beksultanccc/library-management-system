from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.core.database import Base
book_author = Table(
    "book_authors",
    Base.metadata,
    Column("book_id", Integer, ForeignKey("books.book_id")),
    Column("author_id", Integer, ForeignKey("authors.author_id"))
)


class Author(Base):
    __tablename__ = "authors"

    author_id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)

    books = relationship("Book", secondary=book_author, back_populates="authors")


class Category(Base):
    __tablename__ = "categories"

    category_id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    books = relationship("Book", back_populates="category")


class Book(Base):
    __tablename__ = "books"

    book_id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    isbn = Column(String(20), unique=True, nullable=True)
    description = Column(Text, nullable=True)
    publish_year = Column(Integer, nullable=True)
    publisher = Column(String(100), nullable=True)
    language = Column(String(50), default="Қазақша")
    pages = Column(Integer, nullable=True)
    cover_image_url = Column(String(500), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.category_id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    category = relationship("Category", back_populates="books")
    authors = relationship("Author", secondary=book_author, back_populates="books")
    copies = relationship("BookCopy", back_populates="book")
    reservations = relationship("Reservation", back_populates="book")

    def __repr__(self):
        return f"<Book {self.title}>"


class BookCopy(Base):
    __tablename__ = "book_copies"

    copy_id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.book_id"), nullable=False)
    barcode = Column(String(50), unique=True, nullable=False)
    status = Column(String(20), default="available")  # available, borrowed, reserved, maintenance
    location = Column(String(100), nullable=True)
    condition = Column(String(50), default="жақсы")
    acquired_date = Column(DateTime(timezone=True), server_default=func.now())

    book = relationship("Book", back_populates="copies")
    transactions = relationship("Transaction", back_populates="book_copy")

    def __repr__(self):
        return f"<BookCopy {self.barcode} - {self.status}>"