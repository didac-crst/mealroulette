from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from mealroulette.models.household import (
    DEFAULT_HOUSEHOLD_ID,
    DEFAULT_HOUSEHOLD_NAME,
    Household,
    HouseholdMembership,
    HouseholdRole,
    PlatformRole,
    UserPlatformRole,
)
from mealroulette.models.user import User, UserRole


class HouseholdService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_default_household(self) -> Household:
        household = self.db.get(Household, DEFAULT_HOUSEHOLD_ID)
        if household is None:
            raise RuntimeError("Default household is missing; run database migrations.")
        return household

    def ensure_default_household(self) -> Household:
        household = self.db.get(Household, DEFAULT_HOUSEHOLD_ID)
        if household is not None:
            return household

        household = Household(id=DEFAULT_HOUSEHOLD_ID, name=DEFAULT_HOUSEHOLD_NAME)
        self.db.add(household)
        self.db.flush()
        return household

    def get_household(self, household_id: UUID) -> Household:
        household = self.db.get(Household, household_id)
        if household is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Household not found")
        return household

    def rename_household(self, household_id: UUID, name: str) -> Household:
        household = self.get_household(household_id)
        cleaned = name.strip()
        if not cleaned:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Household name is required")
        if len(cleaned) > 128:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Household name is too long")
        household.name = cleaned
        self.db.commit()
        self.db.refresh(household)
        return household

    def provision_platform_admin(self, user: User) -> None:
        self._ensure_platform_admin(user.id)
        self.db.flush()

    def ensure_single_active_membership(self, user_id: UUID, *, exclude_household_id: UUID | None = None) -> None:
        membership = self.active_household_membership(user_id)
        if membership is None:
            return
        if exclude_household_id is not None and membership.household_id == exclude_household_id:
            return
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already belongs to an active household",
        )

    def provision_user_tenancy(self, user: User, *, legacy_role: UserRole) -> HouseholdMembership:
        household = self.ensure_default_household()
        membership = self.db.scalar(
            select(HouseholdMembership).where(
                HouseholdMembership.household_id == household.id,
                HouseholdMembership.user_id == user.id,
            )
        )
        if membership is None:
            membership = HouseholdMembership(
                household_id=household.id,
                user_id=user.id,
                role=(
                    HouseholdRole.household_admin
                    if legacy_role == UserRole.admin
                    else HouseholdRole.household_member
                ),
                active=True,
            )
            self.db.add(membership)

        if legacy_role == UserRole.admin:
            self._ensure_platform_admin(user.id)

        self.db.flush()
        return membership

    def _ensure_platform_admin(self, user_id: UUID) -> None:
        existing = self.db.scalar(
            select(UserPlatformRole).where(
                UserPlatformRole.user_id == user_id,
                UserPlatformRole.role == PlatformRole.platform_admin,
            )
        )
        if existing is None:
            self.db.add(UserPlatformRole(user_id=user_id, role=PlatformRole.platform_admin))

    def active_household_membership(self, user_id: UUID) -> HouseholdMembership | None:
        return self.db.scalar(
            select(HouseholdMembership)
            .where(
                HouseholdMembership.user_id == user_id,
                HouseholdMembership.active.is_(True),
            )
            .order_by(HouseholdMembership.joined_at)
        )

    def resolve_active_household_id(self, user_id: UUID) -> UUID:
        membership = self.active_household_membership(user_id)
        if membership is None:
            raise RuntimeError(f"User {user_id} has no active household membership")
        return membership.household_id

    def list_platform_roles(self, user_id: UUID) -> list[PlatformRole]:
        return list(
            self.db.scalars(select(UserPlatformRole.role).where(UserPlatformRole.user_id == user_id))
        )
