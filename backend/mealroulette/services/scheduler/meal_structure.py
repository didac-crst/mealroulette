from __future__ import annotations

import random
from enum import Enum

from mealroulette.models.enums import MealPlanDishLineRole
from mealroulette.schemas.scheduler import PlanningRulesConfig
from mealroulette.services.scheduler.composition import is_centerpiece_candidate, is_main_candidate
from mealroulette.services.scheduler.types import DishCandidate, SlotAssignment


class MealStructure(str, Enum):
    main_dish = "main_dish"
    composed_pair = "composed_pair"


STRUCTURE_TARGET_MAIN_REASON = "Selected as a complete main because this week already has many composed meals."
STRUCTURE_TARGET_COMPOSED_REASON = "Selected as a composed meal to balance the week's menu mix."
STRUCTURE_FALLBACK_MAIN_REASON = "Selected as a complete main because no suitable composed meal was available."
STRUCTURE_FALLBACK_COMPOSED_REASON = "Selected as a composed meal because no suitable complete main was available."


def assignment_structure(assignment: SlotAssignment) -> MealStructure:
    roles = {line.role for line in assignment.lines}
    if MealPlanDishLineRole.main in roles:
        return MealStructure.main_dish
    if MealPlanDishLineRole.centerpiece in roles and MealPlanDishLineRole.side in roles:
        return MealStructure.composed_pair
    if len(assignment.lines) == 1:
        return MealStructure.main_dish
    return MealStructure.composed_pair


def candidate_primary_structure(candidate: DishCandidate) -> MealStructure:
    if is_main_candidate(candidate):
        return MealStructure.main_dish
    if is_centerpiece_candidate(candidate):
        return MealStructure.composed_pair
    return MealStructure.main_dish


def count_week_structures(
    *,
    fixed_assignments: dict[int, int],
    attempt_assignments: list[SlotAssignment],
    candidates_by_id: dict[int, DishCandidate],
) -> tuple[int, int]:
    composed = 0
    mains = 0

    for assignment in attempt_assignments:
        if assignment_structure(assignment) == MealStructure.composed_pair:
            composed += 1
        else:
            mains += 1

    for dish_id in fixed_assignments.values():
        candidate = candidates_by_id.get(dish_id)
        if candidate is None:
            continue
        if candidate_primary_structure(candidate) == MealStructure.composed_pair:
            composed += 1
        else:
            mains += 1

    return composed, mains


def select_preferred_structure(
    composed_count: int,
    *,
    rules: PlanningRulesConfig,
    rng: random.Random,
) -> tuple[MealStructure, list[str], list[str]]:
    spec = rules.composed_meals_per_week
    reasons: list[str] = []
    codes: list[str] = []

    if composed_count < spec.min:
        reasons.append(STRUCTURE_TARGET_COMPOSED_REASON)
        codes.append("structure_target_composed_pair")
        return MealStructure.composed_pair, reasons, codes

    if composed_count >= spec.max:
        reasons.append(STRUCTURE_TARGET_MAIN_REASON)
        codes.append("structure_target_main")
        return MealStructure.main_dish, reasons, codes

    share = rules.structure_neutral_share
    if rng.random() < share.main:
        return MealStructure.main_dish, reasons, codes
    return MealStructure.composed_pair, reasons, codes
