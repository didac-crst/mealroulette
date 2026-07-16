from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

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
