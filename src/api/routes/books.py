from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.schemas.book import (
    BookCreate, BookResponse, BookUpdate, BookSearchRequest,
    BookSearchResponse, BookCopyCreate, BookCopyResponse,
    AuthorCreate, AuthorResponse, CategoryCreate, CategoryResponse
)
from src.services.book_service import BookService
from src.api.dependencies import get_current_active_user, require_roles

router = APIRouter(prefix="/api/books", tags=["Кітаптар"])


@router.get("/", response_model=BookSearchResponse)
async def search_books(
        query: Optional[str] = Query(None),
        author: Optional[str] = Query(None),
        category: Optional[str] = Query(None),
        year_from: Optional[int] = Query(None),
        year_to: Optional[int] = Query(None),
        language: Optional[str] = Query(None),
        page: int = Query(1, ge=1),
        size: int = Query(20, ge=1, le=100),
        db: Session = Depends(get_db),
        current_user=Depends(get_current_active_user)
):
    search_request = BookSearchRequest(
        query=query,
        author=author,
        category=category,
        year_from=year_from,
        year_to=year_to,
        language=language,
        page=page,
        size=size
    )

    result = await BookService.search_books(db, search_request)
    return result


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(
        book_id: int,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_active_user)
):
    book = await BookService.get_book_by_id(db, book_id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Кітап табылмады"
        )
    return book


@router.post("/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(
        book_data: BookCreate,
        db: Session = Depends(get_db),
        current_user=Depends(require_roles(["admin", "librarian"]))
):
    try:
        book = await BookService.create_book(db, book_data)
        return book
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{book_id}", response_model=BookResponse)
async def update_book(
        book_id: int,
        book_data: BookUpdate,
        db: Session = Depends(get_db),
        current_user=Depends(require_roles(["admin", "librarian"]))
):
    try:
        book = await BookService.update_book(db, book_id, book_data)
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Кітап табылмады"
            )
        return book
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{book_id}")
async def delete_book(
        book_id: int,
        db: Session = Depends(get_db),
        current_user=Depends(require_roles(["admin"]))
):
    success = await BookService.delete_book(db, book_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Кітап табылмады"
        )
    return {"message": "Кітап сәтті жойылды"}


@router.post("/{book_id}/copies", response_model=BookCopyResponse, status_code=status.HTTP_201_CREATED)
async def add_book_copy(
        book_id: int,
        copy_data: BookCopyCreate,
        db: Session = Depends(get_db),
        current_user=Depends(require_roles(["admin", "librarian"]))
):
    try:
        copy = await BookService.add_book_copy(db, book_id, copy_data)
        return copy
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{book_id}/copies", response_model=list[BookCopyResponse])
async def get_book_copies(
        book_id: int,
        status_filter: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        current_user=Depends(get_current_active_user)
):
    copies = await BookService.get_book_copies(db, book_id, status_filter)
    return copies


@router.post("/authors/", response_model=AuthorResponse, status_code=status.HTTP_201_CREATED)
async def create_author(
        author_data: AuthorCreate,
        db: Session = Depends(get_db),
        current_user=Depends(require_roles(["admin", "librarian"]))
):
    author = await BookService.create_author(db, author_data)
    return author


@router.get("/authors/", response_model=list[AuthorResponse])
async def get_authors(
        db: Session = Depends(get_db),
        current_user=Depends(get_current_active_user)
):
    authors = await BookService.get_all_authors(db)
    return authors


@router.post("/categories/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
        category_data: CategoryCreate,
        db: Session = Depends(get_db),
        current_user=Depends(require_roles(["admin", "librarian"]))
):
    category = await BookService.create_category(db, category_data)
    return category


@router.get("/categories/", response_model=list[CategoryResponse])
async def get_categories(
        db: Session = Depends(get_db),
        current_user=Depends(get_current_active_user)
):
    categories = await BookService.get_all_categories(db)
    return categories