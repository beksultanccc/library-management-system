from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime


class AuthorBase(BaseModel):
    full_name: str


class AuthorCreate(AuthorBase):
    pass


class AuthorResponse(AuthorBase):
    author_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class CategoryBase(BaseModel):
    category_name: str
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    category_id: int

    class Config:
        from_attributes = True


class BookBase(BaseModel):
    title: str
    isbn: Optional[str] = None
    description: Optional[str] = None
    publish_year: Optional[int] = None
    publisher: Optional[str] = None
    language: str = "Қазақша"
    pages: Optional[int] = None
    cover_image_url: Optional[str] = None
    category_id: Optional[int] = None


class BookCreate(BookBase):
    author_ids: List[int] = []


class BookUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    publish_year: Optional[int] = None
    publisher: Optional[str] = None
    language: Optional[str] = None
    pages: Optional[int] = None
    cover_image_url: Optional[str] = None
    category_id: Optional[int] = None


class BookResponse(BookBase):
    book_id: int
    authors: List[AuthorResponse] = []
    category: Optional[CategoryResponse] = None
    available_copies: int = 0
    total_copies: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class BookCopyBase(BaseModel):
    book_id: int
    barcode: str
    location: Optional[str] = None
    condition: str = "жақсы"


class BookCopyCreate(BookCopyBase):
    pass


class BookCopyResponse(BookCopyBase):
    copy_id: int
    status: str
    acquired_date: datetime
    book: Optional[BookResponse] = None

    class Config:
        from_attributes = True


class BookSearchRequest(BaseModel):
    query: Optional[str] = None
    author: Optional[str] = None
    category: Optional[str] = None
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    language: Optional[str] = None
    page: int = 1
    size: int = 20


class BookSearchResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[BookResponse]