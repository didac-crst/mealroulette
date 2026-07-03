from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from mealroulette.models.enums import MealSlot, ShoppingListStatus


class ShoppingQuantityComponent(BaseModel):
    quantity: Decimal
    unit_symbol: str


class ShoppingSourceContribution(BaseModel):
    meal_plan_item_id: int
    date: date
    meal_slot: MealSlot
    dish_name: str
    recipe_variant_name: str | None = None
    quantity: Decimal
    unit_symbol: str
    optional: bool = False


class ShoppingSourceMeal(BaseModel):
    meal_plan_item_id: int
    date: date
    meal_slot: MealSlot
    dish_name: str
    recipe_variant_name: str | None = None


class ShoppingPlannedMeal(BaseModel):
    meal_plan_item_id: int
    date: date
    meal_slot: MealSlot
    dish_name: str
    recipe_variant_name: str | None = None


class ShoppingListItemPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    ingredient_id: int
    display_name: str
    quantity: Decimal
    unit_id: int
    unit_symbol: str
    category: str
    checked: bool = False
    approximate: bool = False
    optional: bool = False
    source_meal_plan_item_ids: list[int] = Field(default_factory=list)
    source_meals: list[ShoppingSourceMeal] = Field(default_factory=list)
    source_contributions: list[ShoppingSourceContribution] = Field(default_factory=list)
    raw_components: list[ShoppingQuantityComponent] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ShoppingListPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    from_date: date
    to_date: date
    status: ShoppingListStatus = ShoppingListStatus.active
    exclude_pantry: bool = True
    items: list[ShoppingListItemPublic] = Field(default_factory=list)
    planned_meals: list[ShoppingPlannedMeal] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ShoppingListCreateRequest(BaseModel):
    from_date: date
    days: int = Field(ge=1, le=14)
    exclude_pantry: bool = True


class ShoppingListItemUpdateRequest(BaseModel):
    checked: bool | None = None
