from __future__ import annotations

import random
from dataclasses import dataclass, replace
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
from mealroulette.services.scheduler.meal_structure import (
    STRUCTURE_FALLBACK_COMPOSED_REASON,
    STRUCTURE_FALLBACK_MAIN_REASON,
    MealStructure,
    assignment_structure,
    count_week_structures,
    select_preferred_structure,
)
from mealroulette.services.scheduler.neighbours import build_similarity_neighbours
from mealroulette.services.scheduler.pair_rejections import pair_is_hard_rejected
from mealroulette.services.scheduler.pair_scoring import composed_pair_score_from_prescored
from mealroulette.services.scheduler.reroll_memory import combination_key_from_assignment
from mealroulette.services.scheduler.scoring import score_candidate_for_slot
from mealroulette.services.scheduler.targets import weekly_target_warnings
from mealroulette.services.scheduler.types import (
    DishCandidate,
    GenerationSlot,
    MealNeighbourSnapshot,
    SlotAssignment,
    WeekGenerationResult,
)

MAX_PAIR_CENTERPIECES = 15
MAX_PAIR_SIDES = 25
PAIR_GUARANTEED_TOP_CENTERPIECES = 8
PAIR_RANDOM_CENTERPIECES = 7
PAIR_GUARANTEED_TOP_SIDES = 12
PAIR_RANDOM_SIDES = 13
LARGE_PAIR_SPACE_THRESHOLD = 2_000
TOP_PICK_COUNT = 5


@dataclass(frozen=True)
class _CandidatePartitions:
    mains: list[DishCandidate]
    centerpieces: list[DishCandidate]
    sides: list[DishCandidate]


@dataclass(frozen=True)
class _ScoredCandidate:
    candidate: DishCandidate
    score: float
    payload: dict


@dataclass(frozen=True)
class _SlotPickOption:
    score: float
    assignment: SlotAssignment
    assigned_dish_ids: tuple[int, ...]
    structure: MealStructure


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


def _partition_candidates(candidates: list[DishCandidate]) -> _CandidatePartitions:
    return _CandidatePartitions(
        mains=[candidate for candidate in candidates if is_main_candidate(candidate)],
        centerpieces=[candidate for candidate in candidates if is_centerpiece_candidate(candidate)],
        sides=[candidate for candidate in candidates if is_side_candidate(candidate)],
    )


def _score_eligible_candidates(
    candidates: list[DishCandidate],
    *,
    slot: GenerationSlot,
    assigned_dish_ids: list[int],
    forbidden_dish_ids: frozenset[int] | None,
    dish_date_index: dict[int, list[date]],
    neighbours: list[MealNeighbourSnapshot],
    candidates_by_id: dict[int, DishCandidate],
    rules: PlanningRulesConfig,
) -> list[_ScoredCandidate]:
    scored: list[_ScoredCandidate] = []
    for candidate in candidates:
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
        scored.append(_ScoredCandidate(candidate=candidate, score=score, payload=payload))
    return scored


def _diverse_shortlist(
    scored: list[_ScoredCandidate],
    *,
    max_count: int,
    guaranteed_top: int,
    random_pick: int,
    rng: random.Random,
) -> list[_ScoredCandidate]:
    if len(scored) <= max_count:
        return scored

    ranked = sorted(scored, key=lambda entry: entry.score, reverse=True)
    top_count = min(guaranteed_top, max_count, len(ranked))
    top = ranked[:top_count]
    remaining = ranked[top_count:]
    sample_size = min(random_pick, max_count - top_count, len(remaining))
    sampled = rng.sample(remaining, sample_size) if sample_size > 0 else []
    return top + sampled


def _effective_plan_attempts(rules: PlanningRulesConfig, candidates: list[DishCandidate]) -> int:
    centerpiece_count = sum(1 for candidate in candidates if is_centerpiece_candidate(candidate))
    side_count = sum(1 for candidate in candidates if is_side_candidate(candidate))
    pair_space = centerpiece_count * side_count
    if pair_space <= LARGE_PAIR_SPACE_THRESHOLD:
        return rules.plan_attempts
    if pair_space <= 10_000:
        return min(rules.plan_attempts, max(15, rules.plan_attempts // 2))
    return min(rules.plan_attempts, max(10, rules.plan_attempts // 3))


def _option_is_forbidden(
    option: _SlotPickOption,
    forbidden_combination_keys: frozenset[tuple] | None,
) -> bool:
    if forbidden_combination_keys is None:
        return False
    return combination_key_from_assignment(option.assignment) in forbidden_combination_keys


def _build_main_options(
    slot: GenerationSlot,
    *,
    mains: list[DishCandidate],
    assigned_dish_ids: list[int],
    forbidden_dish_ids: frozenset[int] | None,
    forbidden_combination_keys: frozenset[tuple] | None,
    dish_date_index: dict[int, list[date]],
    neighbours: list[MealNeighbourSnapshot],
    candidates_by_id: dict[int, DishCandidate],
    rules: PlanningRulesConfig,
) -> list[_SlotPickOption]:
    options: list[_SlotPickOption] = []
    for scored in _score_eligible_candidates(
        mains,
        slot=slot,
        assigned_dish_ids=assigned_dish_ids,
        forbidden_dish_ids=forbidden_dish_ids,
        dish_date_index=dish_date_index,
        neighbours=neighbours,
        candidates_by_id=candidates_by_id,
        rules=rules,
    ):
        option = _SlotPickOption(
            score=scored.score,
            assignment=assignment_from_main(
                item_id=slot.item_id,
                candidate=scored.candidate,
                score=scored.score,
                payload=scored.payload,
            ),
            assigned_dish_ids=(scored.candidate.dish_id,),
            structure=MealStructure.main_dish,
        )
        if not _option_is_forbidden(option, forbidden_combination_keys):
            options.append(option)
    return options


def _build_pair_options(
    slot: GenerationSlot,
    *,
    centerpieces: list[DishCandidate],
    sides: list[DishCandidate],
    assigned_dish_ids: list[int],
    forbidden_dish_ids: frozenset[int] | None,
    forbidden_combination_keys: frozenset[tuple] | None,
    dish_date_index: dict[int, list[date]],
    neighbours: list[MealNeighbourSnapshot],
    candidates_by_id: dict[int, DishCandidate],
    rules: PlanningRulesConfig,
    rng: random.Random,
) -> list[_SlotPickOption]:
    options: list[_SlotPickOption] = []

    scored_centerpieces = _score_eligible_candidates(
        centerpieces,
        slot=slot,
        assigned_dish_ids=assigned_dish_ids,
        forbidden_dish_ids=forbidden_dish_ids,
        dish_date_index=dish_date_index,
        neighbours=neighbours,
        candidates_by_id=candidates_by_id,
        rules=rules,
    )
    scored_sides = _score_eligible_candidates(
        sides,
        slot=slot,
        assigned_dish_ids=assigned_dish_ids,
        forbidden_dish_ids=forbidden_dish_ids,
        dish_date_index=dish_date_index,
        neighbours=neighbours,
        candidates_by_id=candidates_by_id,
        rules=rules,
    )

    shortlisted_centerpieces = _diverse_shortlist(
        scored_centerpieces,
        max_count=MAX_PAIR_CENTERPIECES,
        guaranteed_top=PAIR_GUARANTEED_TOP_CENTERPIECES,
        random_pick=PAIR_RANDOM_CENTERPIECES,
        rng=rng,
    )
    shortlisted_sides = _diverse_shortlist(
        scored_sides,
        max_count=MAX_PAIR_SIDES,
        guaranteed_top=PAIR_GUARANTEED_TOP_SIDES,
        random_pick=PAIR_RANDOM_SIDES,
        rng=rng,
    )

    for centerpiece in shortlisted_centerpieces:
        for side in shortlisted_sides:
            if side.candidate.dish_id == centerpiece.candidate.dish_id:
                continue
            if pair_is_hard_rejected(centerpiece.candidate, side.candidate):
                continue
            total_score, payload = composed_pair_score_from_prescored(
                centerpiece.candidate,
                side.candidate,
                centerpiece_score=centerpiece.score,
                centerpiece_payload=centerpiece.payload,
                slot=slot,
                rules=rules,
            )
            option = _SlotPickOption(
                score=total_score,
                assignment=assignment_from_pair(
                    item_id=slot.item_id,
                    centerpiece=centerpiece.candidate,
                    side=side.candidate,
                    score=total_score,
                    payload=payload,
                ),
                assigned_dish_ids=(centerpiece.candidate.dish_id, side.candidate.dish_id),
                structure=MealStructure.composed_pair,
            )
            if not _option_is_forbidden(option, forbidden_combination_keys):
                options.append(option)
    return options


def _build_slot_options(
    slot: GenerationSlot,
    *,
    mains: list[DishCandidate],
    centerpieces: list[DishCandidate],
    sides: list[DishCandidate],
    assigned_dish_ids: list[int],
    forbidden_dish_ids: frozenset[int] | None,
    forbidden_combination_keys: frozenset[tuple] | None,
    dish_date_index: dict[int, list[date]],
    neighbours: list[MealNeighbourSnapshot],
    candidates_by_id: dict[int, DishCandidate],
    rules: PlanningRulesConfig,
    rng: random.Random,
) -> list[_SlotPickOption]:
    """Return all main and pair options (diagnostics/tests). Generation uses structure-first picking."""
    return [
        *_build_main_options(
            slot,
            mains=mains,
            assigned_dish_ids=assigned_dish_ids,
            forbidden_dish_ids=forbidden_dish_ids,
            forbidden_combination_keys=forbidden_combination_keys,
            dish_date_index=dish_date_index,
            neighbours=neighbours,
            candidates_by_id=candidates_by_id,
            rules=rules,
        ),
        *_build_pair_options(
            slot,
            centerpieces=centerpieces,
            sides=sides,
            assigned_dish_ids=assigned_dish_ids,
            forbidden_dish_ids=forbidden_dish_ids,
            forbidden_combination_keys=forbidden_combination_keys,
            dish_date_index=dish_date_index,
            neighbours=neighbours,
            candidates_by_id=candidates_by_id,
            rules=rules,
            rng=rng,
        ),
    ]


def _attach_structure_reasons(option: _SlotPickOption, reasons: list[str], codes: list[str]) -> _SlotPickOption:
    if not reasons and not codes:
        return option
    payload = dict(option.assignment.selection_reasons_json)
    merged_reasons = list(payload.get("reasons", []))
    for reason in reasons:
        if reason not in merged_reasons:
            merged_reasons.append(reason)
    payload["reasons"] = merged_reasons
    if codes:
        payload["structure_reason_codes"] = list(dict.fromkeys([*payload.get("structure_reason_codes", []), *codes]))
    updated_lines = []
    for line in option.assignment.lines:
        if line.selection_reasons_json is None:
            updated_lines.append(line)
            continue
        line_payload = dict(line.selection_reasons_json)
        line_payload["reasons"] = merged_reasons
        if codes:
            line_payload["structure_reason_codes"] = payload["structure_reason_codes"]
        updated_lines.append(replace(line, selection_reasons_json=line_payload))
    updated_assignment = SlotAssignment(
        item_id=option.assignment.item_id,
        lines=tuple(updated_lines),
        score=option.assignment.score,
        selection_reasons_json=payload,
    )
    return _SlotPickOption(
        score=option.score,
        assignment=updated_assignment,
        assigned_dish_ids=option.assigned_dish_ids,
        structure=option.structure,
    )


def _weighted_pick(options: list[_SlotPickOption], rng: random.Random) -> _SlotPickOption:
    ranked = sorted(options, key=lambda entry: entry.score, reverse=True)
    top = ranked[:TOP_PICK_COUNT]
    weights = [max(entry.score, 0.1) for entry in top]
    return rng.choices(top, weights=weights, k=1)[0]


def _pick_slot_option(
    slot: GenerationSlot,
    *,
    mains: list[DishCandidate],
    centerpieces: list[DishCandidate],
    sides: list[DishCandidate],
    assigned_dish_ids: list[int],
    forbidden_dish_ids: frozenset[int] | None,
    forbidden_combination_keys: frozenset[tuple] | None,
    dish_date_index: dict[int, list[date]],
    neighbours: list[MealNeighbourSnapshot],
    candidates_by_id: dict[int, DishCandidate],
    fixed_assignments: dict[int, int],
    attempt_assignments: list[SlotAssignment],
    rules: PlanningRulesConfig,
    rng: random.Random,
) -> _SlotPickOption | None:
    composed_count, _main_count = count_week_structures(
        fixed_assignments=fixed_assignments,
        attempt_assignments=attempt_assignments,
        candidates_by_id=candidates_by_id,
    )
    preferred, structure_reasons, structure_codes = select_preferred_structure(
        composed_count,
        rules=rules,
        rng=rng,
    )

    common_kwargs = dict(
        slot=slot,
        assigned_dish_ids=assigned_dish_ids,
        forbidden_dish_ids=forbidden_dish_ids,
        forbidden_combination_keys=forbidden_combination_keys,
        dish_date_index=dish_date_index,
        neighbours=neighbours,
        candidates_by_id=candidates_by_id,
        rules=rules,
    )
    main_options = _build_main_options(mains=mains, **common_kwargs)
    pair_options = _build_pair_options(
        centerpieces=centerpieces,
        sides=sides,
        rng=rng,
        **common_kwargs,
    )

    if preferred == MealStructure.main_dish:
        if main_options:
            picked = _weighted_pick(main_options, rng)
            return _attach_structure_reasons(picked, structure_reasons, structure_codes)
        if pair_options:
            fallback_reasons = [STRUCTURE_FALLBACK_COMPOSED_REASON, *structure_reasons]
            fallback_codes = ["structure_fallback_no_candidates", *structure_codes]
            picked = _weighted_pick(pair_options, rng)
            return _attach_structure_reasons(picked, fallback_reasons, fallback_codes)
        return None

    if pair_options:
        picked = _weighted_pick(pair_options, rng)
        return _attach_structure_reasons(picked, structure_reasons, structure_codes)
    if main_options:
        fallback_reasons = [STRUCTURE_FALLBACK_MAIN_REASON, *structure_reasons]
        fallback_codes = ["structure_fallback_no_candidates", *structure_codes]
        picked = _weighted_pick(main_options, rng)
        return _attach_structure_reasons(picked, fallback_reasons, fallback_codes)
    return None


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
    forbidden_combination_keys: frozenset[tuple] | None = None,
) -> WeekGenerationResult:
    random_source = rng or random.Random()
    if not slots:
        return WeekGenerationResult(assignments=[], total_score=0.0, warnings=[])

    candidates_by_id = {candidate.dish_id: candidate for candidate in candidates}
    candidate_partitions = _partition_candidates(candidates)
    best_assignments: list[SlotAssignment] = []
    best_score = float("-inf")
    best_warnings: list[str] = []
    plan_attempts = _effective_plan_attempts(rules, candidates)

    ordered_slots = sorted(slots, key=lambda slot: (slot.meal_date, meal_slot_sort_key(slot.meal_slot)))
    slot_dates_by_item = {slot.item_id: slot.meal_date for slot in ordered_slots}
    slot_dates_by_item.update(fixed_dates_by_item)

    for _ in range(plan_attempts):
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

            picked = _pick_slot_option(
                slot,
                mains=candidate_partitions.mains,
                centerpieces=candidate_partitions.centerpieces,
                sides=candidate_partitions.sides,
                assigned_dish_ids=assigned_dish_ids,
                forbidden_dish_ids=forbidden_dish_ids,
                forbidden_combination_keys=forbidden_combination_keys,
                dish_date_index=dish_date_index,
                neighbours=neighbours,
                candidates_by_id=candidates_by_id,
                fixed_assignments=fixed_assignments,
                attempt_assignments=attempt_assignments,
                rules=rules,
                rng=random_source,
            )
            if picked is None:
                failed = True
                break

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
