from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from mealroulette.models.user import UserRole


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=8, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(
        description="Use refresh_token from /login, not access_token.",
    )


class LogoutRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    email: EmailStr
    role: UserRole
    platform_roles: list[str] = Field(default_factory=list)
    active_household_id: UUID | None = None
    active_household_name: str | None = None
    household_role: str | None = None
    active: bool
    created_at: datetime
    updated_at: datetime


class TelegramOtpRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)


class TelegramOtpVerifyRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    code: str = Field(min_length=6, max_length=8)


class UserCreateRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.user
    active: bool = True


class UserUpdateRequest(BaseModel):
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)
    role: UserRole | None = None
    active: bool | None = None
