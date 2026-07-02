from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from mealroulette.auth.dependencies import utcnow
from mealroulette.auth.security import (
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
        if user is None or not verify_password(password, user.password_hash):
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
        user_id = payload.get("sub")
        if not jti or not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        stored_token = self.db.scalar(select(RefreshToken).where(RefreshToken.token_jti == jti))
        if stored_token is None or stored_token.expires_at < utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token revoked or expired",
            )

        user = self.db.get(User, int(user_id))
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
        self.db.delete(user)
        self.db.commit()

    @staticmethod
    def to_public(user: User) -> UserPublic:
        return UserPublic.model_validate(user)
