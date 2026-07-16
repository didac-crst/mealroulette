from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from mealroulette.auth.security import hash_password
from mealroulette.models.household import Household, HouseholdInvitation, HouseholdMembership, HouseholdRole
from mealroulette.models.user import User, UserRole
from mealroulette.services.household import HouseholdService


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class HouseholdMembershipService:
    INVITATION_TTL_HOURS = 72

    def __init__(self, db: Session) -> None:
        self.db = db
        self.household_service = HouseholdService(db)

    def count_active_admins(self, household_id: UUID) -> int:
        return int(
            self.db.scalar(
                select(func.count())
                .select_from(HouseholdMembership)
                .where(
                    HouseholdMembership.household_id == household_id,
                    HouseholdMembership.active.is_(True),
                    HouseholdMembership.role == HouseholdRole.household_admin,
                )
            )
            or 0
        )

    def _lock_household(self, household_id: UUID) -> Household:
        household = self.db.scalar(
            select(Household).where(Household.id == household_id).with_for_update()
        )
        if household is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Household not found")
        return household

    def _lock_active_admins(self, household_id: UUID) -> list[HouseholdMembership]:
        return list(
            self.db.scalars(
                select(HouseholdMembership)
                .where(
                    HouseholdMembership.household_id == household_id,
                    HouseholdMembership.active.is_(True),
                    HouseholdMembership.role == HouseholdRole.household_admin,
                )
                .order_by(HouseholdMembership.id)
                .with_for_update()
            )
        )

    def _ensure_not_last_admin(self, membership: HouseholdMembership) -> None:
        if membership.role != HouseholdRole.household_admin or not membership.active:
            return
        self._lock_household(membership.household_id)
        admins = self._lock_active_admins(membership.household_id)
        if not any(admin.id == membership.id for admin in admins):
            return
        if len(admins) <= 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Household must retain at least one active admin",
            )

    def list_members(self, household_id: UUID) -> list[HouseholdMembership]:
        return list(
            self.db.scalars(
                select(HouseholdMembership)
                .where(
                    HouseholdMembership.household_id == household_id,
                    HouseholdMembership.active.is_(True),
                )
                .order_by(HouseholdMembership.joined_at)
            )
        )

    def get_membership(
        self,
        membership_id: UUID,
        household_id: UUID,
        *,
        for_update: bool = False,
    ) -> HouseholdMembership:
        stmt = select(HouseholdMembership).where(
            HouseholdMembership.id == membership_id,
            HouseholdMembership.household_id == household_id,
        )
        if for_update:
            stmt = stmt.with_for_update()
        membership = self.db.scalar(stmt)
        if membership is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")
        return membership

    def update_member_role(self, membership_id: UUID, household_id: UUID, role: HouseholdRole) -> HouseholdMembership:
        self._lock_household(household_id)
        membership = self.get_membership(membership_id, household_id, for_update=True)
        if membership.role == HouseholdRole.household_admin and role != HouseholdRole.household_admin:
            self._ensure_not_last_admin(membership)
        membership.role = role
        self.db.commit()
        self.db.refresh(membership)
        return membership

    def remove_member(self, membership_id: UUID, household_id: UUID) -> None:
        self._lock_household(household_id)
        membership = self.get_membership(membership_id, household_id, for_update=True)
        self._ensure_not_last_admin(membership)
        membership.active = False
        self.db.commit()

    def create_invitation(self, household_id: UUID, created_by_user_id: UUID) -> tuple[HouseholdInvitation, str]:
        token = secrets.token_urlsafe(32)
        invitation = HouseholdInvitation(
            id=uuid4(),
            household_id=household_id,
            token_hash=_hash_token(token),
            created_by_user_id=created_by_user_id,
            expires_at=datetime.now(UTC) + timedelta(hours=self.INVITATION_TTL_HOURS),
        )
        self.db.add(invitation)
        self.db.commit()
        self.db.refresh(invitation)
        return invitation, token

    def _reject_unclaimable_invitation(self, token: str, *, now: datetime) -> None:
        invitation = self.db.scalar(
            select(HouseholdInvitation).where(HouseholdInvitation.token_hash == _hash_token(token))
        )
        if invitation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")
        if invitation.revoked_at is not None:
            raise HTTPException(status_code=status.HTTP_410_GONE, detail="Invitation revoked")
        if invitation.accepted_at is not None:
            raise HTTPException(status_code=status.HTTP_410_GONE, detail="Invitation already used")
        if invitation.expires_at < now:
            raise HTTPException(status_code=status.HTTP_410_GONE, detail="Invitation expired")
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Invitation already used")

    def _require_claimable_invitation(self, token: str) -> HouseholdInvitation:
        now = datetime.now(UTC)
        invitation = self.db.scalar(
            select(HouseholdInvitation).where(HouseholdInvitation.token_hash == _hash_token(token))
        )
        if invitation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")
        if invitation.revoked_at is not None:
            raise HTTPException(status_code=status.HTTP_410_GONE, detail="Invitation revoked")
        if invitation.accepted_at is not None:
            raise HTTPException(status_code=status.HTTP_410_GONE, detail="Invitation already used")
        if invitation.expires_at < now:
            raise HTTPException(status_code=status.HTTP_410_GONE, detail="Invitation expired")
        return invitation

    def _claim_invitation(self, token: str) -> HouseholdInvitation:
        """Atomically claim a valid invitation before membership/user side effects."""
        now = datetime.now(UTC)
        claimed = self.db.scalars(
            update(HouseholdInvitation)
            .where(
                HouseholdInvitation.token_hash == _hash_token(token),
                HouseholdInvitation.accepted_at.is_(None),
                HouseholdInvitation.revoked_at.is_(None),
                HouseholdInvitation.expires_at >= now,
            )
            .values(accepted_at=now)
            .returning(HouseholdInvitation)
        ).first()
        if claimed is None:
            self._reject_unclaimable_invitation(token, now=now)
            raise AssertionError("unreachable")  # pragma: no cover
        return claimed

    def _lock_user(self, user_id: UUID) -> User:
        user = self.db.scalar(select(User).where(User.id == user_id).with_for_update())
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user

    def accept_invitation_for_user(self, token: str, user: User) -> HouseholdMembership:
        # Serialize same-user acceptance before membership checks/side effects.
        self._lock_user(user.id)
        preview = self._require_claimable_invitation(token)
        self.household_service.ensure_single_active_membership(
            user.id,
            exclude_household_id=preview.household_id,
        )
        invitation = self._claim_invitation(token)
        existing = self.db.scalar(
            select(HouseholdMembership).where(
                HouseholdMembership.household_id == invitation.household_id,
                HouseholdMembership.user_id == user.id,
            )
        )
        if existing is not None:
            if existing.active:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already a household member")
            existing.active = True
            existing.role = HouseholdRole.household_member
            membership = existing
        else:
            membership = HouseholdMembership(
                household_id=invitation.household_id,
                user_id=user.id,
                role=HouseholdRole.household_member,
                active=True,
            )
            self.db.add(membership)
        invitation.accepted_by_user_id = user.id
        self.db.commit()
        self.db.refresh(membership)
        return membership

    def register_with_invitation(
        self,
        *,
        token: str,
        username: str,
        email: str,
        password: str,
    ) -> User:
        invitation = self._claim_invitation(token)
        self._assert_unique_identity(username, email)
        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            role=UserRole.user,
            active=True,
        )
        self.db.add(user)
        self.db.flush()
        self.db.add(
            HouseholdMembership(
                household_id=invitation.household_id,
                user_id=user.id,
                role=HouseholdRole.household_member,
                active=True,
            )
        )
        invitation.accepted_by_user_id = user.id
        self.db.commit()
        self.db.refresh(user)
        return user

    def register_new_household(
        self,
        *,
        username: str,
        email: str,
        password: str,
        household_name: str,
    ) -> User:
        self._assert_unique_identity(username, email)
        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            role=UserRole.user,
            active=True,
        )
        household = Household(id=uuid4(), name=household_name.strip() or "My household")
        self.db.add(user)
        self.db.add(household)
        self.db.flush()
        self.db.add(
            HouseholdMembership(
                household_id=household.id,
                user_id=user.id,
                role=HouseholdRole.household_admin,
                active=True,
            )
        )
        self.db.commit()
        self.db.refresh(user)
        return user

    def list_invitations(self, household_id: UUID) -> list[HouseholdInvitation]:
        return list(
            self.db.scalars(
                select(HouseholdInvitation)
                .where(
                    HouseholdInvitation.household_id == household_id,
                    HouseholdInvitation.revoked_at.is_(None),
                    HouseholdInvitation.accepted_at.is_(None),
                )
                .order_by(HouseholdInvitation.created_at.desc())
            )
        )

    def revoke_invitation(self, invitation_id: UUID, household_id: UUID) -> None:
        now = datetime.now(UTC)
        revoked = self.db.scalars(
            update(HouseholdInvitation)
            .where(
                HouseholdInvitation.id == invitation_id,
                HouseholdInvitation.household_id == household_id,
                HouseholdInvitation.accepted_at.is_(None),
                HouseholdInvitation.revoked_at.is_(None),
            )
            .values(revoked_at=now)
            .returning(HouseholdInvitation)
        ).first()
        if revoked is not None:
            self.db.commit()
            return

        invitation = self.db.get(HouseholdInvitation, invitation_id)
        if invitation is None or invitation.household_id != household_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")
        if invitation.accepted_at is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invitation already accepted")
        # Already revoked: preserve previous idempotent success.
        if invitation.revoked_at is not None:
            return
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")

    def _assert_unique_identity(self, username: str, email: str) -> None:
        if self.db.scalar(select(User).where(User.username == username)):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
        if self.db.scalar(select(User).where(User.email == email)):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
