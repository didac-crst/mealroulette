from datetime import datetime, time
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, model_validator

from mealroulette.models.household import HouseholdRole


class AcceptInvitationRequest(BaseModel):
    token: str = Field(min_length=1)


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    household_name: str = Field(default="My household", min_length=1, max_length=128)


class RegisterWithInvitationRequest(BaseModel):
    token: str = Field(min_length=1)
    username: str = Field(min_length=3, max_length=64)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class HouseholdPublic(BaseModel):
    id: UUID
    name: str

    model_config = {"from_attributes": True}


class UpdateHouseholdRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)


class HouseholdMemberPublic(BaseModel):
    membership_id: UUID
    user_id: UUID
    username: str
    email: EmailStr
    role: HouseholdRole
    joined_at: datetime


class UpdateMemberRoleRequest(BaseModel):
    role: HouseholdRole


class HouseholdInvitationPublic(BaseModel):
    id: UUID
    expires_at: datetime
    created_at: datetime
    accepted_at: datetime | None

    model_config = {"from_attributes": True}


class HouseholdInvitationCreated(BaseModel):
    invitation: HouseholdInvitationPublic
    invite_url: str


class TelegramLinkTokenPublic(BaseModel):
    token: str
    expires_at: datetime
    deep_link_url: str | None = None


class TelegramUserLinkPublic(BaseModel):
    linked: bool
    username: str | None = None
    display_name: str | None = None
    linked_at: datetime | None = None


class NotificationSubscriptionPublic(BaseModel):
    notify_daily_reminder: bool
    notify_shopping: bool
    notify_roulette: bool
    daily_reminder_time: time
    shopping_window_days: int
    timezone: str
    last_reminder_sent_at: datetime | None = None


class NotificationSubscriptionUpdateRequest(BaseModel):
    notify_daily_reminder: bool | None = None
    notify_shopping: bool | None = None
    notify_roulette: bool | None = None
    daily_reminder_time: time | None = None
    shopping_window_days: int | None = Field(default=None, ge=1, le=14)
    timezone: str | None = None

    @model_validator(mode="before")
    @classmethod
    def reject_explicit_nulls(cls, data: object) -> object:
        if isinstance(data, dict):
            for key, value in data.items():
                if value is None:
                    raise ValueError(f"{key} cannot be null")
        return data
