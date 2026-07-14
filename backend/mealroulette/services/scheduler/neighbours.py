from __future__ import annotations

from datetime import date

from mealroulette.services.scheduler.types import DishCandidate, MealNeighbourSnapshot, SlotAssignment


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
        candidate = candidates_by_id.get(assignment.dish_id)
        meal_date = slot_dates_by_item.get(assignment.item_id)
        if candidate is None or meal_date is None:
            continue
        neighbours.append(
            snapshot_from_candidate(
                candidate,
                meal_date=meal_date,
                source="generated",
                item_id=assignment.item_id,
            )
        )
        for line in assignment.lines[1:]:
            side_candidate = candidates_by_id.get(line.dish_id)
            if side_candidate is None:
                continue
            neighbours.append(
                snapshot_from_candidate(
                    side_candidate,
                    meal_date=meal_date,
                    source="generated_side",
                    item_id=assignment.item_id,
                )
            )

    return neighbours
