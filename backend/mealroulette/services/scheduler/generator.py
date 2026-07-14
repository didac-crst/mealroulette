from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date

from mealroulette.schemas.scheduler import PlanningRulesConfig
from mealroulette.services.planning_rules import meal_slot_sort_key
from mealroulette.services.scheduler.composition import (
    assignment_from_main,
    assignment_from_pair,
    is_centerpiece_candidate,
    is_main_candidate,
    is_side_candidate,
)
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

SIDE_PAIR_SCORE_WEIGHT = 0.25


@dataclass(frozen=True)
class _SlotPickOption:
    score: float
    assignment: SlotAssignment
    assigned_dish_ids: tuple[int, ...]


def _candidate_is_eligible(
    candidate: DishCandidate,
    *,
    slot: GenerationSlot,
    assigned_dish_ids: list[int],
    forbidden_dish_ids: frozenset[int] | None,
    dish_date_index: dict[int, list[date]],
    rules: PlanningRulesConfig,
) -> bool:
    if candidate.dish_id in assigned_dish_ids:
        return False
    if forbidden_dish_ids and candidate.dish_id in forbidden_dish_ids:
        return False
    if not passes_slot_suitability(candidate, slot.meal_slot):
        return False
    return passes_same_dish_window(
        candidate,
        slot,
        dish_dates=dish_date_index,
        rules=rules,
    )


def _build_slot_options(
    slot: GenerationSlot,
    *,
    candidates: list[DishCandidate],
    assigned_dish_ids: list[int],
    forbidden_dish_ids: frozenset[int] | None,
    dish_date_index: dict[int, list[date]],
    neighbours: list[MealNeighbourSnapshot],
    candidates_by_id: dict[int, DishCandidate],
    rules: PlanningRulesConfig,
) -> list[_SlotPickOption]:
    options: list[_SlotPickOption] = []

    for candidate in candidates:
        if not is_main_candidate(candidate):
            continue
        if not _candidate_is_eligible(
            candidate,
            slot=slot,
            assigned_dish_ids=assigned_dish_ids,
            forbidden_dish_ids=forbidden_dish_ids,
            dish_date_index=dish_date_index,
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
        options.append(
            _SlotPickOption(
                score=score,
                assignment=assignment_from_main(
                    item_id=slot.item_id,
                    candidate=candidate,
                    score=score,
                    payload=payload,
                ),
                assigned_dish_ids=(candidate.dish_id,),
            )
        )

    centerpieces = [candidate for candidate in candidates if is_centerpiece_candidate(candidate)]
    sides = [candidate for candidate in candidates if is_side_candidate(candidate)]
    for centerpiece in centerpieces:
        if not _candidate_is_eligible(
            centerpiece,
            slot=slot,
            assigned_dish_ids=assigned_dish_ids,
            forbidden_dish_ids=forbidden_dish_ids,
            dish_date_index=dish_date_index,
            rules=rules,
        ):
            continue
        centerpiece_score, centerpiece_payload = score_candidate_for_slot(
            centerpiece,
            slot,
            assigned_dish_ids=assigned_dish_ids,
            candidates_by_id=candidates_by_id,
            neighbours=neighbours,
            rules=rules,
        )
        for side in sides:
            if side.dish_id == centerpiece.dish_id:
                continue
            if not _candidate_is_eligible(
                side,
                slot=slot,
                assigned_dish_ids=[*assigned_dish_ids, centerpiece.dish_id],
                forbidden_dish_ids=forbidden_dish_ids,
                dish_date_index=dish_date_index,
                rules=rules,
            ):
                continue
            side_score, _ = score_candidate_for_slot(
                side,
                slot,
                assigned_dish_ids=[*assigned_dish_ids, centerpiece.dish_id],
                candidates_by_id=candidates_by_id,
                neighbours=neighbours,
                rules=rules,
            )
            total_score = centerpiece_score + (SIDE_PAIR_SCORE_WEIGHT * side_score)
            payload = {
                **centerpiece_payload,
                "reasons": [
                    *centerpiece_payload.get("reasons", []),
                    f"Paired with {side.dish_name}",
                ],
                "score": round(total_score, 3),
                "package_type": "centerpiece_side",
            }
            options.append(
                _SlotPickOption(
                    score=total_score,
                    assignment=assignment_from_pair(
                        item_id=slot.item_id,
                        centerpiece=centerpiece,
                        side=side,
                        score=total_score,
                        payload=payload,
                    ),
                    assigned_dish_ids=(centerpiece.dish_id, side.dish_id),
                )
            )

    return options


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
                (line.dish_id, slot_dates_by_item[assignment.item_id])
                for assignment in attempt_assignments
                for line in assignment.lines
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

            options = _build_slot_options(
                slot,
                candidates=candidates,
                assigned_dish_ids=assigned_dish_ids,
                forbidden_dish_ids=forbidden_dish_ids,
                dish_date_index=dish_date_index,
                neighbours=neighbours,
                candidates_by_id=candidates_by_id,
                rules=rules,
            )
            if not options:
                failed = True
                break

            options.sort(key=lambda entry: entry.score, reverse=True)
            top = options[:5]
            weights = [max(entry.score, 0.1) for entry in top]
            picked = random_source.choices(top, weights=weights, k=1)[0]

            attempt_assignments.append(picked.assignment)
            assigned_dish_ids.extend(picked.assigned_dish_ids)
            attempt_score += picked.score

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
