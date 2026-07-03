from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from mealroulette.models.enums import MealPlanItemStatus, MealPlanStatus, MealSlot


class MealPlanItemPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    meal_plan_id: int
    date: date
    meal_slot: MealSlot
    dish_id: int | None
    recipe_id: int | None
    dish_name: str | None = None
    recipe_variant_name: str | None = None
    status: MealPlanItemStatus
    is_locked: bool
    manually_selected: bool
    skip_reason: str | None
    skip_comment: str | None
    leftover_source_item_id: int | None
    selection_reasons_json: dict | None
    review_saved_at: datetime | None
    created_at: datetime
    updated_at: datetime


class MealPlanPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    week_start_date: date
    status: MealPlanStatus
    items: list[MealPlanItemPublic] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class MealPlanCreateRequest(BaseModel):
    week_start_date: date
    status: MealPlanStatus = MealPlanStatus.active


class MealPlanItemUpdateRequest(BaseModel):
    dish_id: int | None = None
    recipe_id: int | None = None
    status: MealPlanItemStatus | None = None
    is_locked: bool | None = None
    skip_reason: str | None = Field(default=None, max_length=64)
    skip_comment: str | None = None
    leftover_source_item_id: int | None = None


class MealPlanItemSkipRequest(BaseModel):
    skip_reason: str | None = Field(default=None, max_length=64)
    skip_comment: str | None = None


class MealPlanItemAteLeftoversRequest(BaseModel):
    leftover_source_item_id: int | None = None


class MealRatingPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    meal_plan_item_id: int
    dish_id: int
    recipe_id: int | None
    rating: int
    comment: str | None
    created_at: datetime


class MealRatingCreateRequest(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str | None = None


class MealRatingUpsertResponse(BaseModel):
    rating: MealRatingPublic
    item: MealPlanItemPublic
