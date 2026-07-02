from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from mealroulette.core.config import settings


def create_db_engine(database_url: str | None = None) -> Engine:
    return create_engine(
        database_url or settings.database_url,
        pool_pre_ping=True,
    )


engine = create_db_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_connection(db: Session) -> None:
    db.execute(text("SELECT 1"))
