from __future__ import annotations

from mealroulette.models.enums import MealComposition, MealPlanDishLineRole, MealPlanDishLineSource, SimpleDishPart
from mealroulette.models.planning import MealPlanItem
from mealroulette.services.scheduler.types import DishCandidate, SlotAssignment, SlotAssignmentLine


def is_main_candidate(candidate: DishCandidate) -> bool:
    return candidate.meal_composition == MealComposition.main_dish


def is_centerpiece_candidate(candidate: DishCandidate) -> bool:
    return (
        candidate.meal_composition == MealComposition.simple_dish
        and candidate.simple_dish_part == SimpleDishPart.centerpiece
    )


def is_side_candidate(candidate: DishCandidate) -> bool:
    return (
        candidate.meal_composition == MealComposition.simple_dish
        and candidate.simple_dish_part == SimpleDishPart.sidedish
    )


def role_for_candidate(candidate: DishCandidate) -> MealPlanDishLineRole:
    if is_centerpiece_candidate(candidate):
        return MealPlanDishLineRole.centerpiece
    if is_side_candidate(candidate):
        return MealPlanDishLineRole.side
    return MealPlanDishLineRole.main


def assignment_from_main(
    *,
    item_id: int,
    candidate: DishCandidate,
    score: float,
    payload: dict,
) -> SlotAssignment:
    line = SlotAssignmentLine(
        dish_id=candidate.dish_id,
        recipe_id=candidate.recipe_id,
        role=MealPlanDishLineRole.main,
        position=0,
        selection_reasons_json=payload,
    )
    return SlotAssignment(
        item_id=item_id,
        lines=(line,),
        score=score,
        selection_reasons_json=payload,
    )


def assignment_from_pair(
    *,
    item_id: int,
    centerpiece: DishCandidate,
    side: DishCandidate,
    score: float,
    payload: dict,
) -> SlotAssignment:
    return SlotAssignment(
        item_id=item_id,
        lines=(
            SlotAssignmentLine(
                dish_id=centerpiece.dish_id,
                recipe_id=centerpiece.recipe_id,
                role=MealPlanDishLineRole.centerpiece,
                position=0,
                selection_reasons_json=payload,
            ),
            SlotAssignmentLine(
                dish_id=side.dish_id,
                recipe_id=side.recipe_id,
                role=MealPlanDishLineRole.side,
                position=1,
                selection_reasons_json=None,
            ),
        ),
        score=score,
        selection_reasons_json=payload,
    )


def item_has_roulette_lines(item: MealPlanItem) -> bool:
    return any(line.source == MealPlanDishLineSource.roulette for line in item.lines)


def roulette_dish_ids(item: MealPlanItem) -> list[int]:
    return [
        line.dish_id
        for line in item.lines
        if line.source == MealPlanDishLineSource.roulette and line.dish_id is not None
    ]
