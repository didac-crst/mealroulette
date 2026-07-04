from __future__ import annotations

from mealroulette.services.scheduler.similarity import similarity_distance
from mealroulette.services.scheduler.types import MealNeighbourSnapshot


def build_variety_assessment(
    *,
    new_assignments: list[tuple[int, str, dict[str, float]]],
    neighbours: list[MealNeighbourSnapshot],
) -> dict:
    """Build a user-facing variety summary without embedding projection.

    Each new assignment is (dish_id, dish_name, family_vector).
    Neighbours include eaten history and other meals in the plan window.
    """
    if not new_assignments:
        return {"average_distance_to_neighbours": None, "items": []}

    items: list[dict] = []
    distances: list[float] = []

    for dish_id, dish_name, vector in new_assignments:
        if not neighbours:
            items.append(
                {
                    "dish_id": dish_id,
                    "dish_name": dish_name,
                    "nearest_neighbour_dish": None,
                    "distance": None,
                    "variety_label": "no neighbours in window",
                }
            )
            continue

        nearest = min(
            neighbours,
            key=lambda meal: similarity_distance(vector, meal.vector),
        )
        distance = similarity_distance(vector, nearest.vector)
        distances.append(distance)
        items.append(
            {
                "dish_id": dish_id,
                "dish_name": dish_name,
                "nearest_neighbour_dish": nearest.dish_name,
                "nearest_neighbour_date": nearest.meal_date.isoformat(),
                "nearest_neighbour_source": nearest.source,
                "distance": round(distance, 3),
                "variety_label": _variety_label(distance),
            }
        )

    average = round(sum(distances) / len(distances), 3) if distances else None
    return {
        "average_distance_to_neighbours": average,
        "items": items,
    }


def _variety_label(distance: float) -> str:
    if distance >= 0.75:
        return "very different"
    if distance >= 0.45:
        return "moderately different"
    if distance >= 0.25:
        return "somewhat similar"
    return "very similar"
