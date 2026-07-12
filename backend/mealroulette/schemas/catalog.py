from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mealroulette.models.enums import (
    AggregationStrategy,
    ConversionConfidence,
    ConversionSource,
    DifficultyLevel,
    DishCourse,
    DishStatus,
    RecipeType,
    SeasonalityMode,
    SeasonalityStrength,
    ServingTemperature,
    UnitDimension,
    VegetableLevel,
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


class IngredientCategoryPublic(BaseModel):
    id: str
    label: str


class IngredientPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    canonical_name: str
    display_name: str
    category: str | None
    food_group: str | None
    storage_class: str | None = None
    storage_after_opening: str | None = None
    culinary_category: str | None = None
    product_form: str | None = None
    preservation: str | None = None
    traits_json: dict | None = None
    family: str | None
    default_unit_id: int | None
    default_dimension: UnitDimension | None
    preferred_shopping_unit_id: int | None
    aggregation_unit_id: int | None
    aggregation_strategy: AggregationStrategy | None
    pantry_item: bool
    season_start_month: int | None
    season_end_month: int | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class IngredientUnitConversionPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ingredient_id: int
    from_unit_id: int
    to_unit_id: int
    from_unit_symbol: str
    to_unit_symbol: str
    factor: Decimal
    confidence: ConversionConfidence
    notes: str | None
    approved: bool
    source: ConversionSource | None
    created_at: datetime
    updated_at: datetime


class IngredientDetailPublic(IngredientPublic):
    aliases: list["IngredientAliasPublic"] = Field(default_factory=list)
    unit_conversions: list[IngredientUnitConversionPublic] = Field(default_factory=list)


class IngredientCreateRequest(BaseModel):
    canonical_name: str = Field(min_length=1, max_length=128)
    display_name: str = Field(min_length=1, max_length=128)
    category: str | None = Field(default=None, max_length=64)
    food_group: str | None = Field(default=None, max_length=64)
    storage_class: str | None = Field(default=None, max_length=32)
    culinary_category: str | None = Field(default=None, max_length=64)
    product_form: str | None = Field(default=None, max_length=32)
    preservation: str | None = Field(default=None, max_length=32)
    family: str | None = Field(default=None, max_length=64)
    default_unit_id: int | None = None
    default_dimension: UnitDimension | None = None
    preferred_shopping_unit_id: int | None = None
    aggregation_unit_id: int | None = None
    aggregation_strategy: AggregationStrategy | None = None
    pantry_item: bool = False
    season_start_month: int | None = Field(default=None, ge=1, le=12)
    season_end_month: int | None = Field(default=None, ge=1, le=12)
    notes: str | None = None
    aliases: list[str] = Field(default_factory=list)


class IngredientUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=128)
    category: str | None = Field(default=None, max_length=64)
    food_group: str | None = Field(default=None, max_length=64)
    storage_class: str | None = Field(default=None, max_length=32)
    culinary_category: str | None = Field(default=None, max_length=64)
    product_form: str | None = Field(default=None, max_length=32)
    preservation: str | None = Field(default=None, max_length=32)
    family: str | None = Field(default=None, max_length=64)
    default_unit_id: int | None = None
    default_dimension: UnitDimension | None = None
    preferred_shopping_unit_id: int | None = None
    aggregation_unit_id: int | None = None
    aggregation_strategy: AggregationStrategy | None = None
    pantry_item: bool | None = None
    season_start_month: int | None = Field(default=None, ge=1, le=12)
    season_end_month: int | None = Field(default=None, ge=1, le=12)
    notes: str | None = None


class IngredientUnitConversionCreateRequest(BaseModel):
    from_unit_id: int
    to_unit_id: int
    factor: Decimal = Field(gt=0)
    confidence: ConversionConfidence = ConversionConfidence.medium
    notes: str | None = None
    approved: bool = False
    source: ConversionSource = ConversionSource.manual


class IngredientUnitConversionUpdateRequest(BaseModel):
    factor: Decimal | None = Field(default=None, gt=0)
    confidence: ConversionConfidence | None = None
    notes: str | None = None
    approved: bool | None = None
    source: ConversionSource | None = None

    @model_validator(mode="before")
    @classmethod
    def reject_null_non_nullable_fields(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        for field in ("factor", "confidence", "approved"):
            if field in data and data[field] is None:
                raise ValueError(f"{field} cannot be null")
        return data


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
    query: str | None = None
    matched_on: str | None = None
    matched_value: str | None = None
    ingredient: IngredientPublic | None = None
    suggestions: list[IngredientPublic] = Field(default_factory=list)


class IngredientConfirmAction(str, Enum):
    create = "create"
    map = "map"
    alias = "alias"


class IngredientConfirmRequest(BaseModel):
    action: IngredientConfirmAction
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
    quantity: Decimal | None = Field(default=None, ge=0)
    unit_id: int | None = None
    optional: bool = False
    notes: str | None = None


class RecipeIngredientUpdateRequest(BaseModel):
    quantity: Decimal | None = Field(default=None, ge=0)
    unit_id: int | None = None
    optional: bool | None = None
    notes: str | None = None


class RecipePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dish_id: int
    public_key: str
    sequence_number: int
    variant_name: str
    description: str | None
    recipe_type: RecipeType
    is_main: bool
    is_thermomix: bool
    thermomix_model: str | None
    source_url: str | None
    servings: int | None
    prep_time_minutes: int | None
    cook_time_minutes: int | None
    difficulty: DifficultyLevel | None
    computed_traits_json: dict | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class RecipeCreateRequest(BaseModel):
    variant_name: str = Field(min_length=1, max_length=128)
    description: str | None = None
    recipe_type: RecipeType | None = None
    is_main: bool | None = None
    is_thermomix: bool | None = None
    thermomix_model: str | None = Field(default=None, max_length=32)
    source_url: str | None = Field(default=None, max_length=512)
    servings: int | None = Field(default=None, ge=1)
    prep_time_minutes: int | None = Field(default=None, ge=0)
    cook_time_minutes: int | None = Field(default=None, ge=0)
    difficulty: DifficultyLevel | None = None
    notes: str | None = None


class RecipeUpdateRequest(BaseModel):
    variant_name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = None
    recipe_type: RecipeType | None = None
    is_main: bool | None = None
    is_thermomix: bool | None = None
    thermomix_model: str | None = Field(default=None, max_length=32)
    source_url: str | None = Field(default=None, max_length=512)
    servings: int | None = Field(default=None, ge=1)
    prep_time_minutes: int | None = Field(default=None, ge=0)
    cook_time_minutes: int | None = Field(default=None, ge=0)
    difficulty: DifficultyLevel | None = None
    notes: str | None = None


class DishPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    public_key: str
    name: str
    description: str | None
    default_servings: int | None
    default_prep_time_minutes: int | None
    default_cook_time_minutes: int | None
    default_difficulty: DifficultyLevel | None
    course: DishCourse | None
    status: DishStatus
    image_url: str | None
    suitable_for_lunch: bool | None
    suitable_for_dinner: bool | None
    weekday_friendly: bool | None
    leftovers_possible: bool | None
    freezer_friendly: bool | None
    kids_friendly: bool | None
    thermomix_possible: bool | None
    active: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime
    tag_ids: list[int] = Field(default_factory=list)
    computed_traits_json: dict | None = None
    seasonality: SeasonalityPublic | None = None


class DishDetailPublic(DishPublic):
    recipes: list[RecipePublic] = Field(default_factory=list)


class DishCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    default_servings: int | None = Field(default=None, ge=1)
    default_prep_time_minutes: int | None = Field(default=None, ge=0)
    default_cook_time_minutes: int | None = Field(default=None, ge=0)
    default_difficulty: DifficultyLevel | None = None
    course: DishCourse | None = None
    status: DishStatus = DishStatus.active
    image_url: str | None = Field(default=None, max_length=512)
    suitable_for_lunch: bool | None = None
    suitable_for_dinner: bool | None = None
    weekday_friendly: bool | None = None
    leftovers_possible: bool | None = None
    freezer_friendly: bool | None = None
    kids_friendly: bool | None = None
    active: bool = True
    notes: str | None = None
    tag_ids: list[int] = Field(default_factory=list)
    seasonality: SeasonalityUpsertRequest | None = None


class DishUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    default_servings: int | None = Field(default=None, ge=1)
    default_prep_time_minutes: int | None = Field(default=None, ge=0)
    default_cook_time_minutes: int | None = Field(default=None, ge=0)
    default_difficulty: DifficultyLevel | None = None
    course: DishCourse | None = None
    status: DishStatus | None = None
    image_url: str | None = Field(default=None, max_length=512)
    suitable_for_lunch: bool | None = None
    suitable_for_dinner: bool | None = None
    weekday_friendly: bool | None = None
    leftovers_possible: bool | None = None
    freezer_friendly: bool | None = None
    kids_friendly: bool | None = None
    active: bool | None = None
    notes: str | None = None
    tag_ids: list[int] | None = None
    seasonality: SeasonalityUpsertRequest | None = None
