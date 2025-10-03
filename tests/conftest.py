"""
DeepCalm — Test Configuration

Фикстуры для pytest.
Следует cortex/DEEP-CALM-INFRASTRUCTURE.md (Testing)
"""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Generator

if os.getenv("PYTEST_SKIP_DB_FIXTURES") == "1":
    pytest.skip("Skipping DB fixtures for lightweight unit tests", allow_module_level=True)

from app.main import app
from app.core.db import Base, get_db
from app.core.config import settings


# Test database URL (отдельная БД для тестов)
TEST_DATABASE_URL = settings.database_url.replace("deep_calm_dev", "deep_calm_test")

# Test engine
test_engine = create_engine(
    TEST_DATABASE_URL,
    echo=False  # отключаем SQL логи в тестах
)

# Test session factory
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine
)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """
    Создаёт тестовую БД перед всеми тестами.

    Scope: session (один раз за весь запуск pytest)
    """
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db_session() -> Generator:
    """
    Изолированная сессия БД для каждого теста.

    После каждого теста делается rollback, чтобы не влиять на другие тесты.

    Scope: function (новая сессия для каждого теста)

    Yields:
        SQLAlchemy Session

    Examples:
        >>> def test_create_campaign(db_session):
        >>>     campaign = Campaign(title="Test", sku="RELAX-60", ...)
        >>>     db_session.add(campaign)
        >>>     db_session.commit()
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session) -> TestClient:
    """
    FastAPI TestClient с тестовой БД.

    Переопределяет get_db dependency на тестовую сессию.

    Args:
        db_session: Тестовая сессия БД

    Returns:
        TestClient для HTTP запросов

    Examples:
        >>> def test_get_campaigns(client):
        >>>     response = client.get("/api/v1/campaigns")
        >>>     assert response.status_code == 200
    """
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
