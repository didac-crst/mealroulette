from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from mealroulette.models.household import HouseholdMembership, HouseholdRole, PlatformRole, UserPlatformRole
from mealroulette.models.user import User, UserRole


def user_is_platform_admin(db: Session, user: User) -> bool:
    if user.role == UserRole.admin:
        return True
    assigned = db.scalar(
        select(func.count())
        .select_from(UserPlatformRole)
        .where(
            UserPlatformRole.user_id == user.id,
            UserPlatformRole.role == PlatformRole.platform_admin,
        )
    )
    return bool(assigned)


def user_household_role(db: Session, user_id: UUID, household_id: UUID) -> HouseholdRole | None:
    membership = db.scalar(
        select(HouseholdMembership.role).where(
            HouseholdMembership.user_id == user_id,
            HouseholdMembership.household_id == household_id,
            HouseholdMembership.active.is_(True),
        )
    )
    return membership


def user_is_household_admin(db: Session, user_id: UUID, household_id: UUID) -> bool:
    role = user_household_role(db, user_id, household_id)
    return role == HouseholdRole.household_admin


def user_is_household_member(db: Session, user_id: UUID, household_id: UUID) -> bool:
    return user_household_role(db, user_id, household_id) is not None


def access_token_role(db: Session, user: User) -> str:
    if user_is_platform_admin(db, user):
        return PlatformRole.platform_admin.value
    return UserRole.user.value
