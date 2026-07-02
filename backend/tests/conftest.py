from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from mealroulette.core.config import Settings, get_settings
from mealroulette.db.session import get_db
from mealroulette.main import create_app


@pytest.fixture
def settings() -> Settings:
    return Settings(
        database_url="postgresql+psycopg://mealroulette:mealroulette@localhost:5432/mealroulette_test",
        test_database_url="postgresql+psycopg://mealroulette:mealroulette@localhost:5432/mealroulette_test",
    )


@pytest.fixture
def db_engine(settings: Settings):
    engine = create_engine(settings.test_database_url, pool_pre_ping=True)
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine) -> Generator[Session, None, None]:
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection, autoflush=False, autocommit=False)()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    app = create_app()

    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
