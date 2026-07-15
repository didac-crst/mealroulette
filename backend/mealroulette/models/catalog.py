from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from mealroulette.db.base import Base
from mealroulette.models.household import DEFAULT_HOUSEHOLD_ID
from mealroulette.models.enums import (
    AggregationStrategy,
    ConversionConfidence,
    ConversionSource,
    DishCourse,
    DishStatus,
    MealComposition,
    RecipeType,
    SeasonalityMode,
    SeasonalityStrength,
    ServingTemperature,
    SimpleDishPart,
    UnitDimension,
    VegetableLevel,
)


class Unit(Base):
    __tablename__ = "units"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)
    symbol: Mapped[str] = mapped_column(String(16), unique=True)
    dimension: Mapped[UnitDimension] = mapped_column(Enum(UnitDimension, name="unit_dimension"))
    conversion_to_base: Mapped[Decimal] = mapped_column(Numeric(12, 4))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = (UniqueConstraint("family", "name", name="uq_tags_family_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    family: Mapped[str] = mapped_column(String(64))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    dishes: Mapped[list["Dish"]] = relationship(secondary="dish_tags", back_populates="tags")


class Ingredient(Base):
    __tablename__ = "ingredients"

    id: Mapped[int] = mapped_column(primary_key=True)
    canonical_name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(128))
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    food_group: Mapped[str | None] = mapped_column(String(64), nullable=True)
    storage_class: Mapped[str | None] = mapped_column(String(32), nullable=True)
    culinary_category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    product_form: Mapped[str | None] = mapped_column(String(32), nullable=True)
    preservation: Mapped[str | None] = mapped_column(String(32), nullable=True)
    storage_after_opening: Mapped[str | None] = mapped_column(String(32), nullable=True)
    traits_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    default_unit_id: Mapped[int | None] = mapped_column(ForeignKey("units.id"), nullable=True)
    default_dimension: Mapped[UnitDimension | None] = mapped_column(
        Enum(UnitDimension, name="unit_dimension", create_type=False), nullable=True
    )
    pantry_item: Mapped[bool] = mapped_column(Boolean, default=False)
    family: Mapped[str | None] = mapped_column(String(64), nullable=True)
    family_id: Mapped[str | None] = mapped_column(
        ForeignKey("ingredient_families.id", ondelete="SET NULL"), nullable=True, index=True
    )
    preferred_shopping_unit_id: Mapped[int | None] = mapped_column(ForeignKey("units.id"), nullable=True)
    aggregation_unit_id: Mapped[int | None] = mapped_column(ForeignKey("units.id"), nullable=True)
    aggregation_strategy: Mapped[AggregationStrategy | None] = mapped_column(
        Enum(AggregationStrategy, name="aggregation_strategy"), nullable=True
    )
    season_start_month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    season_end_month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    default_unit: Mapped[Unit | None] = relationship(foreign_keys=[default_unit_id])
    preferred_shopping_unit: Mapped[Unit | None] = relationship(foreign_keys=[preferred_shopping_unit_id])
    aggregation_unit: Mapped[Unit | None] = relationship(foreign_keys=[aggregation_unit_id])
    aliases: Mapped[list["IngredientAlias"]] = relationship(back_populates="ingredient", cascade="all, delete-orphan")
    unit_conversions: Mapped[list["IngredientUnitConversion"]] = relationship(
        back_populates="ingredient", cascade="all, delete-orphan"
    )
    ingredient_family: Mapped["IngredientFamily | None"] = relationship(
        "IngredientFamily", foreign_keys=[family_id]
    )


class IngredientAlias(Base):
    __tablename__ = "ingredient_aliases"
    __table_args__ = (UniqueConstraint("alias", name="uq_ingredient_aliases_alias"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    ingredient_id: Mapped[int] = mapped_column(ForeignKey("ingredients.id", ondelete="CASCADE"), index=True)
    alias: Mapped[str] = mapped_column(String(128))
    language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    ingredient: Mapped[Ingredient] = relationship(back_populates="aliases")


class IngredientUnitConversion(Base):
    __tablename__ = "ingredient_unit_conversions"
    __table_args__ = (
        UniqueConstraint(
            "ingredient_id",
            "from_unit_id",
            "to_unit_id",
            name="uq_ingredient_unit_conversions_triplet",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    ingredient_id: Mapped[int] = mapped_column(ForeignKey("ingredients.id", ondelete="CASCADE"), index=True)
    from_unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"))
    to_unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"))
    factor: Mapped[Decimal] = mapped_column(Numeric(12, 4))
    confidence: Mapped[ConversionConfidence] = mapped_column(
        Enum(ConversionConfidence, name="conversion_confidence"), default=ConversionConfidence.approximate
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[ConversionSource | None] = mapped_column(
        Enum(ConversionSource, name="conversion_source"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    ingredient: Mapped[Ingredient] = relationship(back_populates="unit_conversions")
    from_unit: Mapped[Unit] = relationship(foreign_keys=[from_unit_id])
    to_unit: Mapped[Unit] = relationship(foreign_keys=[to_unit_id])


class Dish(Base):
    __tablename__ = "dishes"
    __table_args__ = (
        UniqueConstraint("household_id", "name", name="uq_dishes_household_name"),
        UniqueConstraint("household_id", "public_key", name="uq_dishes_household_public_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    household_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("households.id", ondelete="CASCADE"),
        index=True,
        default=DEFAULT_HOUSEHOLD_ID,
    )
    public_key: Mapped[str] = mapped_column(String(32), index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_servings: Mapped[int | None] = mapped_column(Integer, nullable=True)
    default_prep_time_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    default_cook_time_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    default_difficulty: Mapped[str | None] = mapped_column(String(32), nullable=True)
    course: Mapped[DishCourse | None] = mapped_column(Enum(DishCourse, name="dish_course"), nullable=True)
    meal_composition: Mapped[MealComposition] = mapped_column(
        Enum(MealComposition, name="meal_composition"),
        nullable=False,
        default=MealComposition.main_dish,
        server_default=MealComposition.main_dish.value,
    )
    simple_dish_part: Mapped[SimpleDishPart | None] = mapped_column(
        Enum(SimpleDishPart, name="simple_dish_part"),
        nullable=True,
    )
    status: Mapped[DishStatus] = mapped_column(Enum(DishStatus, name="dish_status"), default=DishStatus.active)
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    vegetable_level: Mapped[VegetableLevel | None] = mapped_column(
        Enum(VegetableLevel, name="vegetable_level"), nullable=True
    )
    dominant_protein: Mapped[str | None] = mapped_column(String(64), nullable=True)
    dominant_carb: Mapped[str | None] = mapped_column(String(64), nullable=True)
    suitable_for_lunch: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    suitable_for_dinner: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    weekday_friendly: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    leftovers_possible: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    freezer_friendly: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    kids_friendly: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    serving_temperature: Mapped[ServingTemperature | None] = mapped_column(
        Enum(ServingTemperature, name="serving_temperature"), nullable=True
    )
    thermomix_possible: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    recipes: Mapped[list["Recipe"]] = relationship(back_populates="dish", cascade="all, delete-orphan")
    tags: Mapped[list[Tag]] = relationship(secondary="dish_tags", back_populates="dishes")
    seasonality: Mapped["DishSeasonality | None"] = relationship(
        back_populates="dish", cascade="all, delete-orphan", uselist=False
    )


class DishTag(Base):
    __tablename__ = "dish_tags"

    dish_id: Mapped[int] = mapped_column(ForeignKey("dishes.id", ondelete="CASCADE"), primary_key=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)


class DishSeasonality(Base):
    __tablename__ = "dish_seasonality"

    id: Mapped[int] = mapped_column(primary_key=True)
    dish_id: Mapped[int] = mapped_column(ForeignKey("dishes.id", ondelete="CASCADE"), unique=True)
    seasonality_mode: Mapped[SeasonalityMode] = mapped_column(
        Enum(SeasonalityMode, name="seasonality_mode"), default=SeasonalityMode.all_year
    )
    preferred_months: Mapped[list[int]] = mapped_column(ARRAY(Integer), default=list)
    allowed_months: Mapped[list[int]] = mapped_column(ARRAY(Integer), default=list)
    excluded_months: Mapped[list[int]] = mapped_column(ARRAY(Integer), default=list)
    seasonality_strength: Mapped[SeasonalityStrength] = mapped_column(
        Enum(SeasonalityStrength, name="seasonality_strength"), default=SeasonalityStrength.neutral
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    dish: Mapped[Dish] = relationship(back_populates="seasonality")


class Recipe(Base):
    __tablename__ = "recipes"
    __table_args__ = (
        UniqueConstraint("dish_id", "variant_name", name="uq_recipes_dish_variant"),
        UniqueConstraint("dish_id", "sequence_number", name="uq_recipes_dish_sequence"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    dish_id: Mapped[int] = mapped_column(ForeignKey("dishes.id", ondelete="CASCADE"), index=True)
    public_key: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    sequence_number: Mapped[int] = mapped_column(Integer)
    variant_name: Mapped[str] = mapped_column(String(128))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    recipe_type: Mapped[RecipeType] = mapped_column(
        Enum(RecipeType, name="recipe_type"), default=RecipeType.standard
    )
    is_main: Mapped[bool] = mapped_column(Boolean, default=False)
    is_thermomix: Mapped[bool] = mapped_column(Boolean, default=False)
    thermomix_model: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    servings: Mapped[int | None] = mapped_column(Integer, nullable=True)
    prep_time_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cook_time_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    difficulty: Mapped[str | None] = mapped_column(String(32), nullable=True)
    computed_traits_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    dish: Mapped[Dish] = relationship(back_populates="recipes")
    steps: Mapped[list["RecipeStep"]] = relationship(back_populates="recipe", cascade="all, delete-orphan")
    ingredients: Mapped[list["RecipeIngredient"]] = relationship(
        back_populates="recipe", cascade="all, delete-orphan"
    )


class RecipeStep(Base):
    __tablename__ = "recipe_steps"
    __table_args__ = (UniqueConstraint("recipe_id", "step_number", name="uq_recipe_steps_recipe_number"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id", ondelete="CASCADE"), index=True)
    step_number: Mapped[int] = mapped_column(Integer)
    instruction: Mapped[str] = mapped_column(Text)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    temperature: Mapped[str | None] = mapped_column(String(64), nullable=True)
    timer_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_thermomix_step: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    recipe: Mapped[Recipe] = relationship(back_populates="steps")


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id", ondelete="CASCADE"), index=True)
    ingredient_id: Mapped[int] = mapped_column(ForeignKey("ingredients.id", ondelete="RESTRICT"), index=True)
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    unit_id: Mapped[int | None] = mapped_column(ForeignKey("units.id"), nullable=True)
    optional: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    recipe: Mapped[Recipe] = relationship(back_populates="ingredients")
    ingredient: Mapped[Ingredient] = relationship()
    unit: Mapped[Unit | None] = relationship()
