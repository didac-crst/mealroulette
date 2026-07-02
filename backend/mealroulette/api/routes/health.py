from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from mealroulette.db.session import check_database_connection, get_db
from mealroulette.schemas.health import HealthResponse, ReadyResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/health/ready", response_model=ReadyResponse)
def readiness(db: Session = Depends(get_db)) -> ReadyResponse:
    check_database_connection(db)
    return ReadyResponse(status="ok", database="ok")
