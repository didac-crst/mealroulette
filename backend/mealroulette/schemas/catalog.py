from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from mealroulette.models.enums import (
    ConversionConfidence,
    SeasonalityMode,
    SeasonalityStrength,
    UnitDimension,
)


class UnitPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    symbol: str
    dimension: UnitDimension
    conversion_to_base: Decimal
    created_at: datetime
    updated_at: datetime


class TagPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    family: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class TagCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    family: str = Field(min_length=1, max_length=64)
    description: str | None = None


class TagUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    family: str | None = Field(default=None, min_length=1, max_length=64)
    description: str | None = None


class IngredientPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    canonical_name: str
    display_name: str
    category: str | None
    default_unit_id: int | None
    default_dimension: UnitDimension | None
    pantry_item: bool
    season_start_month: int | None
    season_end_month: int | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class IngredientCreateRequest(BaseModel):
    canonical_name: str = Field(min_length=1, max_length=128)
    display_name: str = Field(min_length=1, max_length=128)
    category: str | None = Field(default=None, max_length=64)
    default_unit_id: int | None = None
    default_dimension: UnitDimension | None = None
    pantry_item: bool = False
    season_start_month: int | None = Field(default=None, ge=1, le=12)
    season_end_month: int | None = Field(default=None, ge=1, le=12)
    notes: str | None = None
    aliases: list[str] = Field(default_factory=list)


class IngredientUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=128)
    category: str | None = Field(default=None, max_length=64)
    default_unit_id: int | None = None
    default_dimension: UnitDimension | None = None
    pantry_item: bool | None = None
    season_start_month: int | None = Field(default=None, ge=1, le=12)
    season_end_month: int | None = Field(default=None, ge=1, le=12)
    notes: str | None = None


class IngredientAliasPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ingredient_id: int
    alias: str
    language: str | None
    created_at: datetime
    updated_at: datetime


class IngredientAliasCreateRequest(BaseModel):
    alias: str = Field(min_length=1, max_length=128)
    language: str | None = Field(default=None, max_length=16)


class IngredientResolveRequest(BaseModel):
    proposed_name: str = Field(min_length=1, max_length=128)


class IngredientResolveResponse(BaseModel):
    status: str
    ingredient: IngredientPublic | None = None
    suggestions: list[IngredientPublic] = Field(default_factory=list)


class IngredientConfirmAction(str):
    create = "create"
    map_existing = "map"
    add_alias = "alias"


class IngredientConfirmRequest(BaseModel):
    action: str = Field(description="One of: create, map, alias")
    proposed_name: str = Field(min_length=1, max_length=128)
    ingredient_id: int | None = None
    display_name: str | None = Field(default=None, min_length=1, max_length=128)
    category: str | None = None
    default_unit_id: int | None = None
    language: str | None = None


class SeasonalityPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dish_id: int
    seasonality_mode: SeasonalityMode
    preferred_months: list[int]
    allowed_months: list[int]
    excluded_months: list[int]
    seasonality_strength: SeasonalityStrength
    created_at: datetime
    updated_at: datetime


class SeasonalityUpsertRequest(BaseModel):
    seasonality_mode: SeasonalityMode = SeasonalityMode.all_year
    preferred_months: list[int] = Field(default_factory=list)
    allowed_months: list[int] = Field(default_factory=list)
    excluded_months: list[int] = Field(default_factory=list)
    seasonality_strength: SeasonalityStrength = SeasonalityStrength.neutral


class RecipeStepPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    recipe_id: int
    step_number: int
    instruction: str
    duration_seconds: int | None
    temperature: str | None
    timer_seconds: int | None
    is_thermomix_step: bool
    metadata_json: dict | None
    created_at: datetime
    updated_at: datetime


class RecipeStepCreateRequest(BaseModel):
    step_number: int = Field(ge=1)
    instruction: str = Field(min_length=1)
    duration_seconds: int | None = Field(default=None, ge=0)
    temperature: str | None = Field(default=None, max_length=64)
    timer_seconds: int | None = Field(default=None, ge=0)
    is_thermomix_step: bool = False
    metadata_json: dict | None = None


class RecipeStepUpdateRequest(BaseModel):
    step_number: int | None = Field(default=None, ge=1)
    instruction: str | None = Field(default=None, min_length=1)
    duration_seconds: int | None = Field(default=None, ge=0)
    temperature: str | None = Field(default=None, max_length=64)
    timer_seconds: int | None = Field(default=None, ge=0)
    is_thermomix_step: bool | None = None
    metadata_json: dict | None = None


class RecipeIngredientPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    recipe_id: int
    ingredient_id: int
    quantity: Decimal | None
    unit_id: int | None
    optional: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime


class RecipeIngredientCreateRequest(BaseModel):
    ingredient_id: int | None = None
    proposed_name: str | None = Field(default=None, min_length=1, max_length=128)
    quantity: Decimal | None = None
    unit_id: int | None = None
    optional: bool = False
    notes: str | None = None


class RecipeIngredientUpdateRequest(BaseModel):
    quantity: Decimal | None = None
    unit_id: int | None = None
    optional: bool | None = None
    notes: str | None = None


class RecipePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dish_id: int
    variant_name: str
    description: str | None
    is_thermomix: bool
    source_url: str | None
    servings: int | None
    prep_time_minutes: int | None
    cook_time_minutes: int | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class RecipeCreateRequest(BaseModel):
    variant_name: str = Field(min_length=1, max_length=128)
    description: str | None = None
    is_thermomix: bool = False
    source_url: str | None = Field(default=None, max_length=512)
    servings: int | None = Field(default=None, ge=1)
    prep_time_minutes: int | None = Field(default=None, ge=0)
    cook_time_minutes: int | None = Field(default=None, ge=0)
    notes: str | None = None


class RecipeUpdateRequest(BaseModel):
    variant_name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = None
    is_thermomix: bool | None = None
    source_url: str | None = Field(default=None, max_length=512)
    servings: int | None = Field(default=None, ge=1)
    prep_time_minutes: int | None = Field(default=None, ge=0)
    cook_time_minutes: int | None = Field(default=None, ge=0)
    notes: str | None = None


class DishPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    default_servings: int | None
    prep_time_minutes: int | None
    cook_time_minutes: int | None
    difficulty: str | None
    active: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime
    tag_ids: list[int] = Field(default_factory=list)
    seasonality: SeasonalityPublic | None = None


class DishDetailPublic(DishPublic):
    recipes: list[RecipePublic] = Field(default_factory=list)


class DishCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    default_servings: int | None = Field(default=None, ge=1)
    prep_time_minutes: int | None = Field(default=None, ge=0)
    cook_time_minutes: int | None = Field(default=None, ge=0)
    difficulty: str | None = Field(default=None, max_length=32)
    active: bool = True
    notes: str | None = None
    tag_ids: list[int] = Field(default_factory=list)
    seasonality: SeasonalityUpsertRequest | None = None


class DishUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    default_servings: int | None = Field(default=None, ge=1)
    prep_time_minutes: int | None = Field(default=None, ge=0)
    cook_time_minutes: int | None = Field(default=None, ge=0)
    difficulty: str | None = Field(default=None, max_length=32)
    active: bool | None = None
    notes: str | None = None
    tag_ids: list[int] | None = None
    seasonality: SeasonalityUpsertRequest | None = None
