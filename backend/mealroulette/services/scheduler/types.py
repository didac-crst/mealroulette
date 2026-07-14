from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from mealroulette.models.enums import MealComposition, MealPlanDishLineRole, MealSlot, SeasonalityMode, SimpleDishPart
from mealroulette.services.scheduler.pair_diagnostics import CandidatePairSummary


@dataclass(frozen=True)
class DishCandidate:
    dish_id: int
    dish_name: str
    recipe_id: int
    meal_composition: MealComposition
    simple_dish_part: SimpleDishPart | None
    tag_names: frozenset[str]
    protein_tags: frozenset[str]
    carb_tags: frozenset[str]
    style_tags: frozenset[str]
    vector: dict[str, float]
    average_rating: float | None
    seasonality_mode: SeasonalityMode
    preferred_months: frozenset[int]
    suitable_for_lunch: bool | None
    suitable_for_dinner: bool | None
    computed_traits_json: dict | None = None
    pair_summary: CandidatePairSummary | None = None


@dataclass(frozen=True)
class MealNeighbourSnapshot:
    dish_id: int
    dish_name: str
    meal_date: date
    vector: dict[str, float]
    source: str = "eaten"
    item_id: int | None = None


# Backward-compatible alias used by catalog loaders and tests.
EatenMealSnapshot = MealNeighbourSnapshot


@dataclass(frozen=True)
class GenerationSlot:
    item_id: int
    meal_date: date
    meal_slot: MealSlot


@dataclass(frozen=True)
class SlotAssignmentLine:
    dish_id: int
    recipe_id: int
    role: MealPlanDishLineRole
    position: int
    selection_reasons_json: dict | None = None


@dataclass(frozen=True)
class SlotAssignment:
    item_id: int
    lines: tuple[SlotAssignmentLine, ...]
    score: float
    selection_reasons_json: dict

    @property
    def dish_id(self) -> int:
        return self.lines[0].dish_id

    @property
    def recipe_id(self) -> int:
        return self.lines[0].recipe_id


@dataclass
class WeekGenerationResult:
    assignments: list[SlotAssignment]
    total_score: float
    warnings: list[str] = field(default_factory=list)
