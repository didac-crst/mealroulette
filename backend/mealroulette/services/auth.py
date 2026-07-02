from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from mealroulette.auth.dependencies import parse_token_user_id, utcnow
from mealroulette.auth.security import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from mealroulette.models.user import RefreshToken, User, UserRole
from mealroulette.schemas.user import UserCreateRequest, UserPublic, UserUpdateRequest


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
        access_token = create_access_token(user_id=user.id, role=user.role.value)
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


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def _active_admin_count(self) -> int:
        return self.db.scalar(
            select(func.count())
            .select_from(User)
            .where(User.role == UserRole.admin, User.active.is_(True))
        ) or 0

    def _ensure_not_last_active_admin(self, user: User) -> None:
        if user.role == UserRole.admin and user.active and self._active_admin_count() <= 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot remove or demote the last active admin",
            )

    def list_users(self) -> list[User]:
        return list(self.db.scalars(select(User).order_by(User.id)))

    def get_user(self, user_id: int) -> User:
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
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_user(self, user_id: int, payload: UserUpdateRequest) -> User:
        user = self.get_user(user_id)

        demoting_admin = user.role == UserRole.admin and user.active and (
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
        if payload.active is not None:
            user.active = payload.active

        user.updated_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete_user(self, user_id: int) -> None:
        user = self.get_user(user_id)
        self._ensure_not_last_active_admin(user)
        self.db.delete(user)
        self.db.commit()

    @staticmethod
    def to_public(user: User) -> UserPublic:
        return UserPublic.model_validate(user)
