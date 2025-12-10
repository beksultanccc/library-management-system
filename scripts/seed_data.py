
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.database import Base
from src.models.user import Role, User
from src.models.book import Book, Author, Category, BookCopy
from src.core.security import get_password_hash

DATABASE_URL = "postgresql://ulms_user:ulms_password@localhost:5432/ulms_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def seed_roles(db: Session):
    roles = [
        {"role_name": "admin", "permissions": '{"all": true}'},
        {"role_name": "librarian", "permissions": '{"manage_books": true, "manage_transactions": true}'},
        {"role_name": "teacher",
         "permissions": '{"borrow_books": true, "reserve_books": true, "extended_period": true}'},
        {"role_name": "student", "permissions": '{"borrow_books": true, "reserve_books": true}'},
    ]

    for role_data in roles:
        role = Role(**role_data)
        db.add(role)

    db.commit()
    print("✓ Рөлдер енгізілді")


def seed_users(db: Session):
    roles = db.query(Role).all()
    role_map = {role.role_name: role for role in roles}

    users = [
        {
            "username": "admin",
            "email": "admin@university.edu",
            "password": "Admin1!",
            "full_name": "Басты әкімші",
            "role": "admin"
        },
        {
            "username": "librarian1",
            "email": "librarian1@university.edu",
            "password": "Libra1!",
            "full_name": "Кітапханашы Айгерім",
            "role": "librarian"
        },
        {
            "username": "teacher1",
            "email": "teacher1@university.edu",
            "password": "Teac123!",
            "full_name": "Оқытушы Бауыржан",
            "role": "teacher"
        },
        {
            "username": "student1",
            "email": "student1@university.edu",
            "password": "Stud123!",
            "full_name": "Студент Айдана",
            "role": "student"
        },
        {
            "username": "student2",
            "email": "student2@university.edu",
            "password": "Stud123!",
            "full_name": "Студент Ерлан",
            "role": "student"
        },
    ]

    for user_data in users:
        user = User(
            username=user_data["username"],
            email=user_data["email"],
            password_hash=get_password_hash(user_data["password"]),
            full_name=user_data["full_name"],
            role_id=role_map[user_data["role"]].role_id,
            phone_number="+77771234567"
        )
        db.add(user)

    db.commit()
    print("✓ Пайдаланушылар енгізілді")


def seed_authors(db: Session):

    authors = [
        {"full_name": "Абай Құнанбаев", "biography": "Ұлы қазақ ақыны, ойшыл, композитор"},
        {"full_name": "Мұхтар Әуезов", "biography": "Қазақ жазушысы," "Абай жолы" "эпопеясының авторы"},
        {"full_name": "Ілияс Жансүгіров", "biography": "Қазақ ақыны, жазушысы"},
        {"full_name": "Сәкен Сейфуллин", "biography": "Қазақ ақыны, жазушысы, мемлекет қайраткері"},
        {"full_name": "Donald Knuth",
         "biography": "Американдық компьютер ғалымы, The Art of Computer Programming авторы"},
        {"full_name": "Robert C. Martin", "biography": "Американдық инженер, Clean Code авторы"},
    ]

    for author_data in authors:
        author = Author(**author_data)
        db.add(author)

    db.commit()
    print("✓ Авторлар енгізілді")


def seed_categories(db: Session):

    categories = [
        {"category_name": "Әдебиет", "description": "Көркем әдебиет"},
        {"category_name": "Ғылым", "description": "Ғылыми әдебиеттер"},
        {"category_name": "Технология", "description": "Информатика және технология"},
        {"category_name": "Тарих", "description": "Тарихи әдебиеттер"},
        {"category_name": "Философия", "description": "Философиялық еңбектер"},
        {"category_name": "Балалар әдебиеті", "description": "Балаларға арналған кітаптар",},
        {"category_name": "Программирование", "description": "Бағдарламалау туралы кітаптар", },
    ]

    for category_data in categories:
        category = Category(**category_data)
        db.add(category)

    db.commit()
    print("✓ Категориялар енгізілді")


def seed_books(db: Session):

    authors = db.query(Author).all()
    categories = db.query(Category).all()

    books = [
        {
            "title": "Абай жолы",
            "isbn": "978-601-7151-01-2",
            "description": "Мұхтар Әуезовтың Абай Құнанбаев туралы эпопеясы",
            "publish_year": 1942,
            "publisher": "Жазушы",
            "language": "Қазақша",
            "pages": 800,
            "cover_image_url": "https://example.com/abay.jpg",
            "category_id": 1,
            "author_ids": [2]
        },
        {
            "title": "The Art of Computer Programming",
            "isbn": "978-0321751041",
            "description": "Компьютерлік бағдарламалау туралы классикалық еңбек",
            "publish_year": 1968,
            "publisher": "Addison-Wesley",
            "language": "Ағылшынша",
            "pages": 672,
            "cover_image_url": "https://example.com/taocp.jpg",
            "category_id": 7,
            "author_ids": [5]
        },
        {
            "title": "Clean Code",
            "isbn": "978-0132350884",
            "description": "Жақсы бағдарламалық жасақтаманы жазу туралы",
            "publish_year": 2008,
            "publisher": "Prentice Hall",
            "language": "Ағылшынша",
            "pages": 464,
            "cover_image_url": "https://example.com/cleancode.jpg",
            "category_id": 7,
            "author_ids": [6]
        },
        {
            "title": "Қара сөздер",
            "isbn": "978-601-7151-02-9",
            "description": "Абайдың философиялық толғаныстары",
            "publish_year": 1890,
            "publisher": "Қазақ университеті",
            "language": "Қазақша",
            "pages": 200,
            "cover_image_url": "https://example.com/karasozder.jpg",
            "category_id": 1,
            "author_ids": [1]
        },
    ]

    for book_data in books:
        book = Book(
            title=book_data["title"],
            isbn=book_data["isbn"],
            description=book_data["description"],
            publish_year=book_data["publish_year"],
            publisher=book_data["publisher"],
            language=book_data["language"],
            pages=book_data["pages"],
            cover_image_url=book_data["cover_image_url"],
            category_id=book_data["category_id"]
        )

        db.add(book)
        db.flush()
        for author_id in book_data["author_ids"]:
            author = next((a for a in authors if a.author_id == author_id), None)
            if author:
                book.authors.append(author)

        for i in range(1, 4):
            copy = BookCopy(
                book_id=book.book_id,
                barcode=f"{book.isbn}-{i:03d}",
                status="available",
                location=f"Сөре {book.book_id * 10 + i}",
                condition="жақсы"
            )
            db.add(copy)

    db.commit()
    print("✓ Кітаптар енгізілді")


def main():
    db = SessionLocal()

    try:
        print("Тестілеу деректерін енгізу басталды...")

        seed_roles(db)
        seed_authors(db)
        seed_categories(db)
        seed_books(db)
        seed_users(db)

        print("✓ Барлық деректер сәтті енгізілді!")

    except Exception as e:
        print(f"✗ Қате: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()