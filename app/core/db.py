"""
DeepCalm — Database Setup

SQLAlchemy engine и session management.
Sync engine согласно ADR-DC-002 (не async для MVP).
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.pool import QueuePool
from typing import Generator

from app.core.config import settings


# SQLAlchemy Base для моделей
Base = declarative_base()


# Engine с connection pooling
engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,  # проверка соединения перед использованием
    echo=settings.app_debug,  # SQL логи в dev режиме
)


# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency для FastAPI endpoints.

    Yields:
        SQLAlchemy Session

    Examples:
        >>> @app.get("/campaigns")
        >>> def get_campaigns(db: Session = Depends(get_db)):
        >>>     return db.query(Campaign).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Инициализация БД (создание всех таблиц).

    WARNING: В production использовать Alembic миграции!
    Эта функция только для тестов и dev окружения.
    """
    Base.metadata.create_all(bind=engine)
