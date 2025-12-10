from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional
import redis
import json

from ..models.book import Book, Author, Category, BookCopy, book_author
from ..models.user import User
from ..schemas.book import (
    BookCreate, BookResponse, BookUpdate, BookSearchRequest,
    BookSearchResponse, BookCopyCreate, BookCopyResponse,
    AuthorCreate, AuthorResponse, CategoryCreate, CategoryResponse
)
from ..core.config import settings
from ..services.audit_service import AuditService
from ..services.search_service import SearchService


class BookService:
    @staticmethod
    async def search_books(db: Session, search_request: BookSearchRequest) -> BookSearchResponse:
        redis_client = redis.Redis.from_url(settings.REDIS_URL)
        cache_key = f"search:{json.dumps(search_request.dict())}"
        cached_result = redis_client.get(cache_key)

        if cached_result:
            return BookSearchResponse.parse_raw(cached_result)
        search_result = await SearchService.search_books(search_request)

        if search_result and search_result.get("hits", {}).get("total", {}).get("value", 0) > 0:
            book_ids = [hit["_source"]["book_id"] for hit in search_result["hits"]["hits"]]
            books = db.query(Book).filter(Book.book_id.in_(book_ids)).all()
        else:
            query = db.query(Book)

            if search_request.query:
                query = query.filter(
                    or_(
                        Book.title.ilike(f"%{search_request.query}%"),
                        Book.description.ilike(f"%{search_request.query}%")
                    )
                )

            if search_request.author:
                query = query.join(Book.authors).filter(
                    Author.full_name.ilike(f"%{search_request.author}%")
                )

            if search_request.category:
                query = query.join(Book.category).filter(
                    Category.category_name.ilike(f"%{search_request.category}%")
                )

            if search_request.year_from:
                query = query.filter(Book.publish_year >= search_request.year_from)

            if search_request.year_to:
                query = query.filter(Book.publish_year <= search_request.year_to)

            if search_request.language:
                query = query.filter(Book.language == search_request.language)

            total = query.count()
            books = query.offset((search_request.page - 1) * search_request.size) \
                .limit(search_request.size) \
                .all()
        response = BookSearchResponse(
            total=total if 'total' in locals() else len(books),
            page=search_request.page,
            size=search_request.size,
            items=[]
        )

        for book in books:
            available_copies = len([copy for copy in book.copies if copy.status == "available"])
            book_response = BookResponse(
                book_id=book.book_id,
                title=book.title,
                isbn=book.isbn,
                description=book.description,
                publish_year=book.publish_year,
                publisher=book.publisher,
                language=book.language,
                pages=book.pages,
                cover_image_url=book.cover_image_url,
                category_id=book.category_id,
                authors=[AuthorResponse.from_orm(author) for author in book.authors],
                category=CategoryResponse.from_orm(book.category) if book.category else None,
                available_copies=available_copies,
                total_copies=len(book.copies),
                created_at=book.created_at
            )
            response.items.append(book_response)

        redis_client.setex(cache_key, 300, response.json())

        return response

    @staticmethod
    async def get_book_by_id(db: Session, book_id: int) -> Optional[BookResponse]:
        redis_client = redis.Redis.from_url(settings.REDIS_URL)
        cache_key = f"book:{book_id}"
        cached_book = redis_client.get(cache_key)

        if cached_book:
            return BookResponse.parse_raw(cached_book)

        book = db.query(Book).filter(Book.book_id == book_id).first()
        if not book:
            return None

        available_copies = len([copy for copy in book.copies if copy.status == "available"])
        book_response = BookResponse(
            book_id=book.book_id,
            title=book.title,
            isbn=book.isbn,
            description=book.description,
            publish_year=book.publish_year,
            publisher=book.publisher,
            language=book.language,
            pages=book.pages,
            cover_image_url=book.cover_image_url,
            category_id=book.category_id,
            authors=[AuthorResponse.from_orm(author) for author in book.authors],
            category=CategoryResponse.from_orm(book.category) if book.category else None,
            available_copies=available_copies,
            total_copies=len(book.copies),
            created_at=book.created_at
        )

        redis_client.setex(cache_key, 600, book_response.json())

        return book_response

    @staticmethod
    async def create_book(db: Session, book_data: BookCreate) -> BookResponse:

        if book_data.category_id:
            category = db.query(Category).filter(Category.category_id == book_data.category_id).first()
            if not category:
                raise ValueError("Категория табылмады")

        authors = []
        for author_id in book_data.author_ids:
            author = db.query(Author).filter(Author.author_id == author_id).first()
            if not author:
                raise ValueError(f"Автор ID {author_id} табылмады")
            authors.append(author)

        book = Book(
            title=book_data.title,
            isbn=book_data.isbn,
            description=book_data.description,
            publish_year=book_data.publish_year,
            publisher=book_data.publisher,
            language=book_data.language,
            pages=book_data.pages,
            cover_image_url=book_data.cover_image_url,
            category_id=book_data.category_id
        )

        db.add(book)
        db.flush()

        book.authors = authors

        db.commit()
        db.refresh(book)

        await SearchService.index_book(book)

        redis_client = redis.Redis.from_url(settings.REDIS_URL)
        redis_client.delete("search:*")

        await AuditService.log_action(
            db,
            user_id=None,  # Админ/кітапханашы user_id болады
            action="book_created",
            details={"book_id": book.book_id, "title": book.title}
        )

        return await BookService.get_book_by_id(db, book.book_id)

    @staticmethod
    async def create_author(db: Session, author_data: AuthorCreate) -> AuthorResponse:
        author = Author(
            full_name=author_data.full_name,
        )

        db.add(author)
        db.commit()
        db.refresh(author)

        return AuthorResponse.from_orm(author)

    @staticmethod
    async def get_all_authors(db: Session) -> List[AuthorResponse]:

        authors = db.query(Author).all()
        return [AuthorResponse.from_orm(author) for author in authors]

    @staticmethod
    async def create_category(db: Session, category_data: CategoryCreate) -> CategoryResponse:

        category = Category(
            category_name=category_data.category_name,
            description=category_data.description
        )

        db.add(category)
        db.commit()
        db.refresh(category)

        return CategoryResponse.from_orm(category)

    @staticmethod
    async def get_all_categories(db: Session) -> List[CategoryResponse]:

        categories = db.query(Category).all()
        return [CategoryResponse.from_orm(category) for category in categories]

    @staticmethod
    async def add_book_copy(db: Session, book_id: int, copy_data: BookCopyCreate) -> BookCopyResponse:

        book = db.query(Book).filter(Book.book_id == book_id).first()
        if not book:
            raise ValueError("Кітап табылмады")

        existing_copy = db.query(BookCopy).filter(BookCopy.barcode == copy_data.barcode).first()
        if existing_copy:
            raise ValueError("Бұл баркод бұрыннан бар")

        copy = BookCopy(
            book_id=book_id,
            barcode=copy_data.barcode,
            location=copy_data.location,
            condition=copy_data.condition,
            status="available"
        )

        db.add(copy)
        db.commit()
        db.refresh(copy)

        redis_client = redis.Redis.from_url(settings.REDIS_URL)
        redis_client.delete(f"book:{book_id}")

        await AuditService.log_action(
            db,
            user_id=None,
            action="book_copy_added",
            details={"copy_id": copy.copy_id, "book_id": book_id, "barcode": copy_data.barcode}
        )

        return BookCopyResponse(
            copy_id=copy.copy_id,
            book_id=copy.book_id,
            barcode=copy.barcode,
            location=copy.location,
            condition=copy.condition,
            status=copy.status,
            acquired_date=copy.acquired_date
        )

    @staticmethod
    async def get_book_copies(db: Session, book_id: int, status_filter: Optional[str] = None) -> List[BookCopyResponse]:
        query = db.query(BookCopy).filter(BookCopy.book_id == book_id)

        if status_filter:
            query = query.filter(BookCopy.status == status_filter)

        copies = query.all()

        result = []
        for copy in copies:
            result.append(BookCopyResponse(
                copy_id=copy.copy_id,
                book_id=copy.book_id,
                barcode=copy.barcode,
                location=copy.location,
                condition=copy.condition,
                status=copy.status,
                acquired_date=copy.acquired_date
            ))

        return result