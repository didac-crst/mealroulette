from __future__ import annotations

from datetime import date

from mealroulette.services.scheduler.composition import (
    aggregate_meal_vector,
    assignment_meal_label,
    assignment_line_candidates,
)
from mealroulette.services.scheduler.types import DishCandidate, MealNeighbourSnapshot, SlotAssignment


def snapshot_from_meal_package(
    *,
    candidates: list[DishCandidate],
    meal_date: date,
    source: str,
    item_id: int | None = None,
    primary_dish_id: int | None = None,
    meal_label: str | None = None,
) -> MealNeighbourSnapshot | None:
    if not candidates:
        return None
    primary_id = primary_dish_id if primary_dish_id is not None else candidates[0].dish_id
    label = meal_label
    if label is None:
        label = candidates[0].dish_name if len(candidates) == 1 else " + ".join(
            candidate.dish_name for candidate in candidates
        )
        if len(candidates) == 2:
            label = f"{candidates[0].dish_name} with {candidates[1].dish_name}"
    return MealNeighbourSnapshot(
        dish_id=primary_id,
        dish_name=label,
        meal_date=meal_date,
        vector=aggregate_meal_vector(candidates),
        source=source,
        item_id=item_id,
    )


def snapshot_from_candidate(
    candidate: DishCandidate,
    *,
    meal_date: date,
    source: str,
    item_id: int | None = None,
) -> MealNeighbourSnapshot:
    return MealNeighbourSnapshot(
        dish_id=candidate.dish_id,
        dish_name=candidate.dish_name,
        meal_date=meal_date,
        vector=candidate.vector,
        source=source,
        item_id=item_id,
    )


def build_similarity_neighbours(
    *,
    eaten_meals: list[MealNeighbourSnapshot],
    fixed_assignments: dict[int, int],
    fixed_dates_by_item: dict[int, date],
    attempt_assignments: list[SlotAssignment],
    slot_dates_by_item: dict[int, date],
    candidates_by_id: dict[int, DishCandidate],
    exclude_item_id: int | None = None,
) -> list[MealNeighbourSnapshot]:
    """Merge eaten history with in-plan neighbours for similarity scoring."""
    neighbours: list[MealNeighbourSnapshot] = list(eaten_meals)

    for item_id, dish_id in fixed_assignments.items():
        if item_id == exclude_item_id:
            continue
        candidate = candidates_by_id.get(dish_id)
        meal_date = fixed_dates_by_item.get(item_id)
        if candidate is None or meal_date is None:
            continue
        neighbours.append(
            snapshot_from_candidate(candidate, meal_date=meal_date, source="planned", item_id=item_id)
        )

    for assignment in attempt_assignments:
        if assignment.item_id == exclude_item_id:
            continue
        meal_date = slot_dates_by_item.get(assignment.item_id)
        if meal_date is None:
            continue
        line_candidates = assignment_line_candidates(assignment, candidates_by_id)
        snapshot = snapshot_from_meal_package(
            candidates=line_candidates,
            meal_date=meal_date,
            source="generated",
            item_id=assignment.item_id,
            primary_dish_id=assignment.dish_id,
            meal_label=assignment_meal_label(assignment, candidates_by_id),
        )
        if snapshot is not None:
            neighbours.append(snapshot)

    return neighbours
