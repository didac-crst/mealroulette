from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from mealroulette.auth.security import hash_password
from mealroulette.core.config import Settings, get_settings
from mealroulette.db.base import Base
from mealroulette.db.session import get_db
from mealroulette.main import create_app
from mealroulette.models.user import User, UserRole
import mealroulette.models  # noqa: F401


@pytest.fixture
def settings() -> Settings:
    return Settings(
        database_url="postgresql+psycopg://mealroulette:mealroulette@localhost:5432/mealroulette_test",
        test_database_url="postgresql+psycopg://mealroulette:mealroulette@localhost:5432/mealroulette_test",
        secret_key="test-secret-key-that-is-long-enough-for-hs256",
    )


@pytest.fixture
def db_engine(settings: Settings):
    engine = create_engine(settings.test_database_url, pool_pre_ping=True)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_session(db_engine) -> Generator[Session, None, None]:
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection, join_transaction_mode="create_savepoint")()

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


@pytest.fixture
def admin_user(db_session: Session) -> User:
    user = User(
        username="admin",
        email="admin@example.com",
        password_hash=hash_password("adminpassword"),
        role=UserRole.admin,
        active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def regular_user(db_session: Session) -> User:
    user = User(
        username="household",
        email="household@example.com",
        password_hash=hash_password("userpassword"),
        role=UserRole.user,
        active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_token(client: TestClient, admin_user: User) -> str:
    response = client.post(
        "/api/auth/login",
        json={"username": admin_user.username, "password": "adminpassword"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def user_token(client: TestClient, regular_user: User) -> str:
    response = client.post(
        "/api/auth/login",
        json={"username": regular_user.username, "password": "userpassword"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
