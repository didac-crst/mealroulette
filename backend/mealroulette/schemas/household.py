from datetime import datetime, time
from uuid import UUID

from pydantic import BaseModel, Field

from mealroulette.models.household import HouseholdRole


class AcceptInvitationRequest(BaseModel):
    token: str = Field(min_length=1)


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    email: str = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    household_name: str = Field(default="My household", max_length=128)


class RegisterWithInvitationRequest(BaseModel):
    token: str
    username: str = Field(min_length=3, max_length=64)
    email: str = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)


class HouseholdMemberPublic(BaseModel):
    membership_id: UUID
    user_id: UUID
    username: str
    email: str
    role: HouseholdRole
    joined_at: datetime

    model_config = {"from_attributes": True}


class HouseholdInvitationPublic(BaseModel):
    id: UUID
    expires_at: datetime
    created_at: datetime
    accepted_at: datetime | None

    model_config = {"from_attributes": True}


class HouseholdInvitationCreated(BaseModel):
    invitation: HouseholdInvitationPublic
    invite_url: str


class UpdateMemberRoleRequest(BaseModel):
    role: HouseholdRole


class HouseholdPublic(BaseModel):
    id: UUID
    name: str

    model_config = {"from_attributes": True}


class UpdateHouseholdRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)


class IngredientProposalCreateRequest(BaseModel):
    proposed_name: str = Field(min_length=1, max_length=128)
    reason: str | None = None


class IngredientProposalPublic(BaseModel):
    id: UUID
    household_id: UUID
    proposed_by_user_id: UUID
    proposed_name: str
    reason: str | None
    status: str
    reviewed_at: datetime | None
    review_note: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class IngredientProposalReviewRequest(BaseModel):
    approve: bool
    review_note: str | None = None


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
