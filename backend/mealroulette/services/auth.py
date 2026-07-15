from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from mealroulette.auth.dependencies import parse_token_user_id, utcnow
from mealroulette.auth.roles import access_token_role, user_is_platform_admin
from mealroulette.auth.security import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from mealroulette.models.household import Household, PlatformRole, UserPlatformRole
from mealroulette.models.user import RefreshToken, User, UserRole
from mealroulette.schemas.user import UserCreateRequest, UserPublic, UserUpdateRequest
from mealroulette.services.household import HouseholdService


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def authenticate(self, username: str, password: str) -> User:
        user = self.db.scalar(select(User).where(User.username == username))
        if user is None:
            verify_password(password, DUMMY_PASSWORD_HASH)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )
        if not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )
        if not user.active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive",
            )
        return user

    def issue_tokens(self, user: User) -> tuple[str, str]:
        access_token = create_access_token(user_id=user.id, role=access_token_role(self.db, user))
        refresh_token, jti, expires_at = create_refresh_token(user_id=user.id)
        self.db.add(RefreshToken(user_id=user.id, token_jti=jti, expires_at=expires_at))
        self.db.commit()
        return access_token, refresh_token

    def refresh(self, refresh_token: str) -> tuple[str, str]:
        try:
            payload = decode_token(refresh_token)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            ) from exc

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        jti = payload.get("jti")
        if not jti:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        user_id = parse_token_user_id(payload.get("sub"))

        stored_token = self.db.scalar(select(RefreshToken).where(RefreshToken.token_jti == jti))
        if stored_token is None or stored_token.expires_at < utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token revoked or expired",
            )

        user = self.db.get(User, user_id)
        if user is None or not user.active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        self.db.delete(stored_token)
        self.db.commit()
        return self.issue_tokens(user)

    def logout(self, refresh_token: str) -> None:
        try:
            payload = decode_token(refresh_token)
        except Exception:
            return

        jti = payload.get("jti")
        if not jti:
            return

        stored_token = self.db.scalar(select(RefreshToken).where(RefreshToken.token_jti == jti))
        if stored_token is not None:
            self.db.delete(stored_token)
            self.db.commit()

    def change_password(self, user: User, *, current_password: str, new_password: str) -> None:
        if not verify_password(current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )
        if current_password == new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from the current password",
            )
        user.password_hash = hash_password(new_password)
        user.updated_at = datetime.now(UTC)
        # Invalidate existing refresh tokens so other sessions must sign in again.
        self.db.execute(delete(RefreshToken).where(RefreshToken.user_id == user.id))
        self.db.commit()


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.household_service = HouseholdService(db)

    def _active_platform_admin_count(self) -> int:
        active_users = self.db.scalars(select(User).where(User.active.is_(True)))
        return sum(1 for user in active_users if user_is_platform_admin(self.db, user))

    def _ensure_not_last_active_admin(self, user: User) -> None:
        if user.active and user_is_platform_admin(self.db, user) and self._active_platform_admin_count() <= 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot remove or demote the last active admin",
            )

    def list_users(self) -> list[User]:
        return list(self.db.scalars(select(User).order_by(User.created_at)))

    def get_user(self, user_id: UUID) -> User:
        user = self.db.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user

    def create_user(self, payload: UserCreateRequest) -> User:
        if self.db.scalar(select(User).where(User.username == payload.username)):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
        if self.db.scalar(select(User).where(User.email == payload.email)):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

        user = User(
            username=payload.username,
            email=payload.email,
            password_hash=hash_password(payload.password),
            role=payload.role,
            active=payload.active,
        )
        self.db.add(user)
        self.db.flush()
        if payload.role == UserRole.admin:
            self.household_service.provision_platform_admin(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_user(self, user_id: UUID, payload: UserUpdateRequest) -> User:
        user = self.get_user(user_id)

        demoting_admin = user.active and user_is_platform_admin(self.db, user) and (
            (payload.role is not None and payload.role != UserRole.admin)
            or (payload.active is not None and not payload.active)
        )
        if demoting_admin:
            self._ensure_not_last_active_admin(user)

        if payload.email is not None:
            existing = self.db.scalar(select(User).where(User.email == payload.email, User.id != user_id))
            if existing is not None:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
            user.email = payload.email
        if payload.password is not None:
            user.password_hash = hash_password(payload.password)
        if payload.role is not None:
            user.role = payload.role
            self._sync_tenancy_roles(user)
        if payload.active is not None:
            user.active = payload.active

        user.updated_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete_user(self, user_id: UUID) -> None:
        user = self.get_user(user_id)
        self._ensure_not_last_active_admin(user)
        self.db.delete(user)
        self.db.commit()

    def _sync_tenancy_roles(self, user: User) -> None:
        if user.role == UserRole.admin:
            self.household_service.provision_platform_admin(user)
        else:
            self.db.execute(
                delete(UserPlatformRole).where(
                    UserPlatformRole.user_id == user.id,
                    UserPlatformRole.role == PlatformRole.platform_admin,
                )
            )

    def to_public(self, user: User) -> UserPublic:
        platform_roles = [role.value for role in self.household_service.list_platform_roles(user.id)]
        if user.role == UserRole.admin and PlatformRole.platform_admin.value not in platform_roles:
            platform_roles.append(PlatformRole.platform_admin.value)
        membership = self.household_service.active_household_membership(user.id)
        household_name = None
        if membership is not None:
            household = self.db.get(Household, membership.household_id)
            household_name = household.name if household is not None else None
        return UserPublic(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            platform_roles=platform_roles,
            active_household_id=membership.household_id if membership is not None else None,
            active_household_name=household_name,
            household_role=membership.role.value if membership is not None else None,
            active=user.active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
