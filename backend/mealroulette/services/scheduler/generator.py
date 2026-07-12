from __future__ import annotations

import random
from datetime import date

from mealroulette.schemas.scheduler import PlanningRulesConfig
from mealroulette.services.planning_rules import meal_slot_sort_key
from mealroulette.services.scheduler.constraints import (
    build_dish_date_index,
    passes_same_dish_window,
    passes_slot_suitability,
)
from mealroulette.services.scheduler.neighbours import build_similarity_neighbours
from mealroulette.services.scheduler.scoring import score_candidate_for_slot
from mealroulette.services.scheduler.targets import weekly_target_warnings
from mealroulette.services.scheduler.types import (
    DishCandidate,
    GenerationSlot,
    MealNeighbourSnapshot,
    SlotAssignment,
    WeekGenerationResult,
)


def generate_week_assignments(
    slots: list[GenerationSlot],
    candidates: list[DishCandidate],
    *,
    fixed_assignments: dict[int, int],
    fixed_dates_by_item: dict[int, date],
    eaten_meals: list[MealNeighbourSnapshot],
    rules: PlanningRulesConfig,
    today: date,
    rng: random.Random | None = None,
    forbidden_dish_ids: frozenset[int] | None = None,
) -> WeekGenerationResult:
    random_source = rng or random.Random()
    if not slots:
        return WeekGenerationResult(assignments=[], total_score=0.0, warnings=[])

    candidates_by_id = {candidate.dish_id: candidate for candidate in candidates}
    best_assignments: list[SlotAssignment] = []
    best_score = float("-inf")
    best_warnings: list[str] = []

    ordered_slots = sorted(slots, key=lambda slot: (slot.meal_date, meal_slot_sort_key(slot.meal_slot)))
    slot_dates_by_item = {slot.item_id: slot.meal_date for slot in ordered_slots}
    slot_dates_by_item.update(fixed_dates_by_item)

    for _ in range(rules.plan_attempts):
        attempt_assignments: list[SlotAssignment] = []
        attempt_score = 0.0
        assigned_dish_ids = [dish_id for dish_id in fixed_assignments.values()]
        failed = False
        for slot in ordered_slots:
            planned_dish_dates = [
                (dish_id, fixed_dates_by_item[item_id]) for item_id, dish_id in fixed_assignments.items()
            ] + [
                (assignment.dish_id, slot_dates_by_item[assignment.item_id])
                for assignment in attempt_assignments
            ]
            dish_date_index = build_dish_date_index(eaten_meals, planned_dish_dates)
            neighbours = build_similarity_neighbours(
                eaten_meals=eaten_meals,
                fixed_assignments=fixed_assignments,
                fixed_dates_by_item=fixed_dates_by_item,
                attempt_assignments=attempt_assignments,
                slot_dates_by_item=slot_dates_by_item,
                candidates_by_id=candidates_by_id,
                exclude_item_id=slot.item_id,
            )

            eligible: list[tuple[DishCandidate, float, dict]] = []
            for candidate in candidates:
                if candidate.dish_id in assigned_dish_ids:
                    continue
                if forbidden_dish_ids and candidate.dish_id in forbidden_dish_ids:
                    continue
                if not passes_slot_suitability(candidate, slot.meal_slot):
                    continue
                if not passes_same_dish_window(
                    candidate,
                    slot,
                    dish_dates=dish_date_index,
                    rules=rules,
                ):
                    continue

                score, payload = score_candidate_for_slot(
                    candidate,
                    slot,
                    assigned_dish_ids=assigned_dish_ids,
                    candidates_by_id=candidates_by_id,
                    neighbours=neighbours,
                    rules=rules,
                )
                eligible.append((candidate, score, payload))

            if not eligible:
                failed = True
                break

            eligible.sort(key=lambda entry: entry[1], reverse=True)
            top = eligible[:5]
            weights = [max(entry[1], 0.1) for entry in top]
            picked, picked_score, payload = random_source.choices(top, weights=weights, k=1)[0]

            attempt_assignments.append(
                SlotAssignment(
                    item_id=slot.item_id,
                    dish_id=picked.dish_id,
                    recipe_id=picked.recipe_id,
                    score=picked_score,
                    selection_reasons_json=payload,
                )
            )
            assigned_dish_ids.append(picked.dish_id)
            attempt_score += picked_score

        if failed:
            continue

        warnings = weekly_target_warnings(
            assigned_dish_ids,
            candidates_by_id=candidates_by_id,
            rules=rules,
        )
        if attempt_score > best_score:
            best_score = attempt_score
            best_assignments = attempt_assignments
            best_warnings = warnings

    if not best_assignments:
        return WeekGenerationResult(
            assignments=[],
            total_score=0.0,
            warnings=["Could not generate a valid plan with current rules and catalog"],
        )

    return WeekGenerationResult(
        assignments=best_assignments,
        total_score=best_score,
        warnings=best_warnings,
    )
