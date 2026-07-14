from collections.abc import Generator
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import Session, sessionmaker

from mealroulette.auth.security import hash_password
from mealroulette.core.config import Settings, get_settings
from mealroulette.data.seed_catalog import seed_catalog_data
from mealroulette.data.seed_taxonomy import seed_taxonomy_data
from mealroulette.db.base import Base
from mealroulette.db.session import get_db
from mealroulette.main import create_app
from mealroulette.models.user import User, UserRole
import mealroulette.models  # noqa: F401


def _test_database_url() -> str:
    worker = os.environ.get("PYTEST_XDIST_WORKER")
    database_name = "mealroulette_test" if worker in (None, "master") else f"mealroulette_test_{worker}"
    base_url = os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql+psycopg://mealroulette:mealroulette@localhost:5432/mealroulette_test",
    )
    return make_url(base_url).set(database=database_name).render_as_string(hide_password=False)


@pytest.fixture
def settings() -> Settings:
    test_url = _test_database_url()
    return Settings(
        database_url=test_url,
        test_database_url=test_url,
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


@pytest.fixture
def catalog_seed(db_session: Session):
    seed_catalog_data(db_session)
    seed_taxonomy_data(db_session)
    return db_session


@pytest.fixture
def scheduler_seed(db_session: Session):
    from mealroulette.data.default_planning_rules import DEFAULT_PLANNING_RULES_JSON, DEFAULT_PLANNING_RULE_NAME
    from mealroulette.models.scheduler import (
        DEFAULT_PLANNING_RULE_ID,
        SCHEDULER_SETTINGS_ID,
        PlanningRule,
        SchedulerSettings,
    )

    if db_session.get(PlanningRule, DEFAULT_PLANNING_RULE_ID) is None:
        db_session.add(
            PlanningRule(
                id=DEFAULT_PLANNING_RULE_ID,
                name=DEFAULT_PLANNING_RULE_NAME,
                active=True,
                rules_json=DEFAULT_PLANNING_RULES_JSON,
            )
        )
    if db_session.get(SchedulerSettings, SCHEDULER_SETTINGS_ID) is None:
        db_session.add(SchedulerSettings(id=SCHEDULER_SETTINGS_ID))
    db_session.commit()
    return db_session


@pytest.fixture
def admin_headers(admin_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def user_headers(user_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture(autouse=True)
def clear_settings_cache(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-that-is-long-enough-for-hs256")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:TEST-BOT-TOKEN")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
