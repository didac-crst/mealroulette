from datetime import UTC, datetime
from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from mealroulette.auth.roles import user_is_household_admin, user_is_platform_admin
from mealroulette.auth.security import decode_token
from mealroulette.db.session import get_db
from mealroulette.models.user import User
from mealroulette.services.catalog import CatalogService
from mealroulette.services.household import HouseholdService
from mealroulette.services.planning import PlanningService
from mealroulette.services.scheduler_service import SchedulerService
from mealroulette.services.shopping import ShoppingListService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)


@dataclass(frozen=True)
class HouseholdScope:
    household_id: UUID


def parse_token_user_id(subject: str | int | None) -> UUID:
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
        )
    try:
        return UUID(str(subject))
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
        ) from exc


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        payload = decode_token(token)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = parse_token_user_id(payload.get("sub"))

    user = db.get(User, user_id)
    if user is None or not user.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user


def get_current_household_scope(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HouseholdScope:
    try:
        household_id = HouseholdService(db).resolve_active_household_id(current_user.id)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No active household membership",
        ) from exc
    return HouseholdScope(household_id=household_id)


def get_planning_service(
    db: Session = Depends(get_db),
    scope: HouseholdScope = Depends(get_current_household_scope),
) -> PlanningService:
    return PlanningService(db, scope.household_id)


def get_scheduler_service(
    db: Session = Depends(get_db),
    scope: HouseholdScope = Depends(get_current_household_scope),
) -> SchedulerService:
    return SchedulerService(db, scope.household_id)


def get_catalog_service(
    db: Session = Depends(get_db),
    scope: HouseholdScope = Depends(get_current_household_scope),
) -> CatalogService:
    return CatalogService(db, scope.household_id)


def get_shopping_service(
    db: Session = Depends(get_db),
    scope: HouseholdScope = Depends(get_current_household_scope),
) -> ShoppingListService:
    return ShoppingListService(db, scope.household_id)


def get_current_platform_admin(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    if not user_is_platform_admin(db, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform admin access required",
        )
    return current_user


def get_current_household_admin(
    scope: HouseholdScope = Depends(get_current_household_scope),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    if not user_is_household_admin(db, current_user.id, scope.household_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Household admin access required",
        )
    return current_user


def get_current_admin(
    current_user: User = Depends(get_current_platform_admin),
) -> User:
    """Deprecated alias — use get_current_platform_admin."""
    return current_user


def utcnow() -> datetime:
    return datetime.now(UTC)
