from __future__ import annotations

from mealroulette.models.enums import MealComposition, MealPlanDishLineRole, MealPlanDishLineSource, SimpleDishPart
from mealroulette.models.planning import MealPlanItem
from mealroulette.services.scheduler.types import DishCandidate, SlotAssignment, SlotAssignmentLine


def _candidate_trait_grams(candidate: DishCandidate) -> float:
    traits = candidate.computed_traits_json or {}
    grams = traits.get("total_trait_grams")
    if isinstance(grams, (int, float)) and grams > 0:
        return float(grams)
    return 1.0


def aggregate_meal_vector(candidates: list[DishCandidate]) -> dict[str, float]:
    if not candidates:
        return {}
    if len(candidates) == 1:
        return dict(candidates[0].vector)

    total_weight = sum(_candidate_trait_grams(candidate) for candidate in candidates)
    if total_weight <= 0:
        total_weight = float(len(candidates))

    combined: dict[str, float] = {}
    for candidate in candidates:
        weight = _candidate_trait_grams(candidate) / total_weight
        for key, value in candidate.vector.items():
            combined[key] = combined.get(key, 0.0) + (value * weight)
    return combined


def assignment_line_candidates(
    assignment: SlotAssignment,
    candidates_by_id: dict[int, DishCandidate],
) -> list[DishCandidate]:
    ordered = sorted(assignment.lines, key=lambda line: line.position)
    return [
        candidates_by_id[line.dish_id]
        for line in ordered
        if line.dish_id in candidates_by_id
    ]


def assignment_meal_label(
    assignment: SlotAssignment,
    candidates_by_id: dict[int, DishCandidate],
) -> str:
    ordered = sorted(assignment.lines, key=lambda line: line.position)
    names = [
        candidates_by_id[line.dish_id].dish_name
        for line in ordered
        if line.dish_id in candidates_by_id
    ]
    if not names:
        return "Unassigned"
    if len(names) == 1:
        return names[0]
    if len(ordered) == 2:
        roles = {line.role for line in ordered}
        if roles == {MealPlanDishLineRole.centerpiece, MealPlanDishLineRole.side}:
            centerpiece = next(line for line in ordered if line.role == MealPlanDishLineRole.centerpiece)
            side = next(line for line in ordered if line.role == MealPlanDishLineRole.side)
            cp_name = candidates_by_id.get(centerpiece.dish_id)
            side_name = candidates_by_id.get(side.dish_id)
            if cp_name is not None and side_name is not None:
                return f"{cp_name.dish_name} with {side_name.dish_name}"
    return " + ".join(names)


def assignment_meal_vector(
    assignment: SlotAssignment,
    candidates_by_id: dict[int, DishCandidate],
) -> dict[str, float]:
    return aggregate_meal_vector(assignment_line_candidates(assignment, candidates_by_id))


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
