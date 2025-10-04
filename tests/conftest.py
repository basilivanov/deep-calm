"""Pytest fixtures and helpers for DeepCalm backend tests."""
from __future__ import annotations

import os
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import url as sa_url
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.db import Base, get_db
from app.core.config import settings


def _resolve_test_database_url() -> str:
    env_url = os.getenv("TEST_DATABASE_URL")
    if env_url:
        return env_url

    base_url = sa_url.make_url(settings.database_url)
    db_name = base_url.database or "deep_calm_dev"
    if not db_name.endswith("_test"):
        db_name = f"{db_name}_test"
    return str(base_url.set(database=db_name))


TEST_DATABASE_URL = _resolve_test_database_url()


def _ensure_database_exists(url_str: str) -> None:
    url = sa_url.make_url(url_str)
    admin_url = url.set(database="postgres")
    engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": url.database},
            ).scalar()
            if not exists:
                owner = url.username or "dc"
                escaped_db = (url.database or "deep_calm_test").replace('"', '""')
                escaped_owner = owner.replace('"', '""')
                conn.execute(
                    text(f'CREATE DATABASE "{escaped_db}" OWNER "{escaped_owner}"')
                )
    except ProgrammingError:
        # База уже создана другим процессом
        pass
    except OperationalError as exc:
        raise RuntimeError(
            "Не удалось создать тестовую БД. Убедитесь, что Postgres запущен или задайте TEST_DATABASE_URL."
        ) from exc
    finally:
        engine.dispose()


_ensure_database_exists(TEST_DATABASE_URL)

test_engine = create_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db_session() -> Generator:
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def client(db_session) -> TestClient:
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
