from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _require_trimmed_nonblank(value: object, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} must not be blank")
    return cleaned


def _trim_optional_text(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("value must be a string")
    cleaned = value.strip()
    return cleaned or None


class PublicRecipeStatusValue(str, Enum):
    submitted = "submitted"
    public = "public"
    rejected = "rejected"
    withdrawn = "withdrawn"
    delisted = "delisted"


class PublicRecipeVersionPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    version_number: int
    published_at: datetime | None
    superseded_at: datetime | None
    created_at: datetime


class PublicRecipeSnapshotIngredient(BaseModel):
    ingredient_id: int
    ingredient_canonical_name: str
    ingredient_display_name: str
    quantity: Decimal | None = None
    unit_id: int | None = None
    unit_symbol: str | None = None
    unit_name: str | None = None
    optional: bool = False
    notes: str | None = None


class PublicRecipeSnapshotStep(BaseModel):
    step_number: int
    instruction: str
    duration_seconds: int | None = None
    temperature: str | None = None
    timer_seconds: int | None = None
    is_thermomix_step: bool = False
    metadata_json: dict[str, Any] | None = None


class PublicRecipeMemberPublic(BaseModel):
    """Authenticated-public catalog DTO — no originating household/user fields."""

    id: UUID
    status: PublicRecipeStatusValue
    title: str
    description: str | None
    current_version: PublicRecipeVersionPublic
    snapshot: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class PublicRecipeHouseholdPublic(BaseModel):
    """Household publication-request DTO — includes review status and originating ids."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: PublicRecipeStatusValue
    originating_dish_id: int
    originating_recipe_id: int
    current_version_id: UUID | None
    title: str
    description: str | None
    review_note: str | None
    reviewed_at: datetime | None
    latest_version: PublicRecipeVersionPublic | None
    created_at: datetime
    updated_at: datetime


class PublicRecipePlatformPublic(BaseModel):
    """Platform moderation DTO — includes originating household and submitter."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: PublicRecipeStatusValue
    originating_household_id: UUID
    originating_dish_id: int
    originating_recipe_id: int
    current_version_id: UUID | None
    submitted_by_user_id: UUID
    reviewed_by_user_id: UUID | None
    reviewed_at: datetime | None
    review_note: str | None
    title: str
    description: str | None
    latest_version: PublicRecipeVersionPublic | None
    current_version: PublicRecipeVersionPublic | None
    snapshot: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class PublicRecipeApproveRequest(BaseModel):
    review_note: str | None = Field(default=None, max_length=4000)

    @field_validator("review_note", mode="before")
    @classmethod
    def trim_optional_note(cls, value: object) -> str | None:
        return _trim_optional_text(value)


class PublicRecipeReviewNoteRequest(BaseModel):
    """Required explanation for reject / delist."""

    review_note: str = Field(..., min_length=1, max_length=4000)

    @field_validator("review_note", mode="before")
    @classmethod
    def review_note_must_be_non_blank(cls, value: object) -> str:
        return _require_trimmed_nonblank(value, field_name="review_note")


class PublicRecipeAdoptResponse(BaseModel):
    dish_id: int
    recipe_id: int
    dish_public_key: str
    recipe_public_key: str
    derived_from_public_recipe_id: UUID
    derived_from_public_version_id: UUID
