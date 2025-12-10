import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://ulms_user:ulms_password@localhost:5432/ulms_db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    ELASTICSEARCH_URL: str = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")

    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"

    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8000"]

    DEFAULT_BORROW_DAYS: int = 14
    MAX_BORROW_DAYS: int = 30
    RESERVATION_EXPIRE_DAYS: int = 7

    FINE_PER_DAY: float = 50.0
    MAX_FINE_AMOUNT: float = 5000.0

    class Config:
        env_file = ".env"


settings = Settings()