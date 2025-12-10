from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import time
import logging

from .core.config import settings
from .core.database import get_db, init_db
from .api.routes import auth, books, transactions, notifications
from .services.audit_service import AuditService
from .services.search_service import SearchService

logging.basicConfig(
    level=logging.INFO if settings.ENVIRONMENT == "production" else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Университеттік кітапхана ақпараттық жүйесі (ULMS)",
    description="Университет кітапханасын басқаруға арналған API",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router)
app.include_router(books.router)
app.include_router(transactions.router)
app.include_router(notifications.router)


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):

    try:
        db.execute("SELECT 1")

        import redis
        redis_client = redis.Redis.from_url(settings.REDIS_URL)
        redis_client.ping()

        es_client = SearchService.get_client()
        es_client.ping()

        return {
            "status": "healthy",
            "database": "connected",
            "redis": "connected",
            "elasticsearch": "connected",
            "environment": settings.ENVIRONMENT
        }
    except Exception as e:
        logger.error(f"Денсаулық тексеру қатесі: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@app.get("/")
async def root():
    return {
        "message": "Университеттік кітапхана ақпараттық жүйесіне қош келдіңіз!",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.on_event("startup")
async def startup_event():
    logger.info("Қолданба іске қосылуда...")

    init_db()
    logger.info("Дерекқор инициализацияланды")

    try:
        await SearchService.create_index()
        logger.info("Elasticsearch индексі құрылды")
    except Exception as e:
        logger.warning(f"Elasticsearch индексін құру қатесі: {e}")

    await seed_default_data()
    logger.info("Әдепкі деректер енгізілді")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Қолданба тоқтатылуда...")


async def seed_default_data():
    from sqlalchemy.orm import sessionmaker
    from .core.database import engine
    from .models.user import Role, User
    from .core.security import get_password_hash

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        roles = [
            {"role_name": "admin", "permissions": '{"all": true}'},
            {"role_name": "librarian", "permissions": '{"manage_books": true, "manage_transactions": true}'},
            {"role_name": "teacher", "permissions": '{"borrow_books": true, "reserve_books": true}'},
            {"role_name": "student", "permissions": '{"borrow_books": true, "reserve_books": true}'},
        ]

        for role_data in roles:
            role = db.query(Role).filter(Role.role_name == role_data["role_name"]).first()
            if not role:
                role = Role(**role_data)
                db.add(role)

        db.commit()

        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            admin_role = db.query(Role).filter(Role.role_name == "admin").first()
            if admin_role:
                admin_user = User(
                    username="admin",
                    email="admin@university.edu",
                    password_hash=get_password_hash("Admin1!"),
                    full_name="Басты әкімші",
                    role_id=admin_role.role_id
                )
                db.add(admin_user)

        db.commit()
        logger.info("Әдепкі деректер сәтті енгізілді")

    except Exception as e:
        logger.error(f"Әдепкі деректерді енгізу қатесі: {e}")
        db.rollback()
    finally:
        db.close()