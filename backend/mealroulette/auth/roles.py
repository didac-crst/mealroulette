from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from mealroulette.models.household import PlatformRole, UserPlatformRole
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


def access_token_role(db: Session, user: User) -> str:
    if user_is_platform_admin(db, user):
        return PlatformRole.platform_admin.value
    return UserRole.user.value
