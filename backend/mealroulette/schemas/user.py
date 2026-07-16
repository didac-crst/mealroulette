from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field

from mealroulette.models.household import HouseholdRole, PlatformRole
from mealroulette.models.user import UserRole

BCRYPT_MAX_PASSWORD_BYTES = 72


def _validate_password_utf8_bytes(value: str) -> str:
    if len(value.encode("utf-8")) > BCRYPT_MAX_PASSWORD_BYTES:
        raise ValueError(f"Password must be at most {BCRYPT_MAX_PASSWORD_BYTES} bytes")
    return value


PasswordStr = Annotated[
    str,
    Field(min_length=8, max_length=128),
    AfterValidator(_validate_password_utf8_bytes),
]


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: PasswordStr


class RefreshRequest(BaseModel):
    refresh_token: str = Field(
        description="Use refresh_token from /login, not access_token.",
    )


class LogoutRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: PasswordStr
    new_password: PasswordStr


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    email: EmailStr
    role: UserRole
    platform_roles: list[PlatformRole] = Field(default_factory=list)
    active_household_id: UUID | None = None
    active_household_name: str | None = None
    household_role: HouseholdRole | None = None
    active: bool
    created_at: datetime
    updated_at: datetime


class UserCreateRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    email: EmailStr
    password: PasswordStr
    role: UserRole = UserRole.user
    active: bool = True


class UserUpdateRequest(BaseModel):
    email: EmailStr | None = None
    password: PasswordStr | None = None
    role: UserRole | None = None
    active: bool | None = None
