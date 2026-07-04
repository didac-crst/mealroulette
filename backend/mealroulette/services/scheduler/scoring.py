from __future__ import annotations

from mealroulette.models.enums import SeasonalityMode
from mealroulette.schemas.scheduler import PlanningRulesConfig
from mealroulette.services.scheduler.similarity import shared_family_keys, similarity_distance
from mealroulette.services.scheduler.targets import weekly_target_score_delta
from mealroulette.services.scheduler.types import DishCandidate, GenerationSlot, MealNeighbourSnapshot


def seasonality_score(candidate: DishCandidate, *, month: int, prefer_seasonal: bool) -> tuple[float, str | None]:
    if not prefer_seasonal:
        return 0.0, None
    if candidate.seasonality_mode == SeasonalityMode.all_year:
        return 0.2, "Seasonally neutral dish"
    if month in candidate.preferred_months:
        return 1.0, f"Good seasonal match for month {month}"
    return -0.3, None


def rating_score(candidate: DishCandidate, *, prefer_high_rated: bool) -> tuple[float, str | None]:
    if not prefer_high_rated or candidate.average_rating is None:
        return 0.0, None
    normalized = candidate.average_rating / 5.0
    reason = None
    if candidate.average_rating >= 4:
        reason = f"Household rating {candidate.average_rating:.1f}/5"
    return normalized, reason


def temporal_weight(days_apart: int, *, window_days: int) -> float:
    if days_apart < 0:
        return 0.0
    if window_days <= 0:
        return 1.0
    return max(0.2, 1.0 - (days_apart / window_days))


def neighbour_similarity_penalty(
    candidate: DishCandidate,
    slot: GenerationSlot,
    *,
    neighbours: list[MealNeighbourSnapshot],
    rules: PlanningRulesConfig,
) -> tuple[float, list[str]]:
    reasons: list[str] = []
    max_penalty = 0.0
    max_distance = 0.0

    for meal in neighbours:
        days_apart = abs((slot.meal_date - meal.meal_date).days)
        if days_apart > rules.avoid_similar_meals_within_days:
            continue

        distance = similarity_distance(candidate.vector, meal.vector)
        similarity = 1.0 - distance
        max_distance = max(max_distance, distance)
        weight = temporal_weight(days_apart, window_days=rules.history_window_days)
        max_penalty = max(max_penalty, weight * similarity)

        if similarity >= rules.similarity_threshold:
            shared = shared_family_keys(candidate.vector, meal.vector, min_pct=5.0)
            shared_label = ", ".join(shared[:3]) if shared else "similar ingredient mix"
            reasons.append(
                f"Similar to {meal.dish_name} on {meal.meal_date.isoformat()} ({shared_label})"
            )

    if max_distance >= 0.45 and not reasons:
        reasons.insert(0, f"Good variety vs neighbouring meals (min distance {max_distance:.2f})")

    return max_penalty, reasons


def score_candidate_for_slot(
    candidate: DishCandidate,
    slot: GenerationSlot,
    *,
    assigned_dish_ids: list[int],
    neighbours: list[MealNeighbourSnapshot],
    rules: PlanningRulesConfig,
) -> tuple[float, dict]:
    month = slot.meal_date.month
    reasons: list[str] = []

    season_score, season_reason = seasonality_score(candidate, month=month, prefer_seasonal=rules.prefer_seasonal)
    rating_component, rating_reason = rating_score(candidate, prefer_high_rated=rules.prefer_high_rated)
    target_delta, target_reasons = weekly_target_score_delta(
        candidate,
        assigned_dish_ids=assigned_dish_ids,
        rules=rules,
    )
    similarity_penalty, similarity_reasons = neighbour_similarity_penalty(
        candidate,
        slot,
        neighbours=neighbours,
        rules=rules,
    )

    total = season_score + rating_component + target_delta - (similarity_penalty * 2.0)
    if season_reason:
        reasons.append(season_reason)
    if rating_reason:
        reasons.append(rating_reason)
    reasons.extend(target_reasons)
    reasons.extend(similarity_reasons[:2])

    relevant_neighbours = [
        meal
        for meal in neighbours
        if abs((slot.meal_date - meal.meal_date).days) <= rules.avoid_similar_meals_within_days
    ]
    payload = {
        "reasons": reasons,
        "score": round(total, 3),
        "similarity_distance_max": round(
            max(
                (similarity_distance(candidate.vector, meal.vector) for meal in relevant_neighbours),
                default=0.0,
            ),
            3,
        ),
    }
    return total, payload
