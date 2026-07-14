#!/usr/bin/env python3
"""Simulate sequential rerolls per slot and inspect option pools (read-only)."""

from __future__ import annotations

import argparse
import random
from collections import Counter
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from mealroulette.db.session import SessionLocal
from mealroulette.models.planning import MealPlan, MealPlanItem
from mealroulette.services.household_time import household_local_today
from mealroulette.services.planning import PlanningService
from mealroulette.services.planning_rule_service import PlanningRuleService
from mealroulette.services.scheduler.catalog import load_dish_candidates, load_eaten_meal_snapshots
from mealroulette.services.scheduler.composition import (
    is_centerpiece_candidate,
    is_main_candidate,
    is_side_candidate,
)
from mealroulette.services.scheduler.constraints import slot_is_regenerable
from mealroulette.services.scheduler.generator import _build_main_options, _build_pair_options, generate_week_assignments
from mealroulette.services.scheduler.meal_structure import (
    MealStructure,
    assignment_structure,
    candidate_primary_structure,
    count_week_structures,
    select_preferred_structure,
)
from mealroulette.services.scheduler.neighbours import build_similarity_neighbours
from mealroulette.services.scheduler.reroll_memory import (
    combination_key_from_assignment,
    forbidden_combination_keys,
)
from mealroulette.services.scheduler.types import GenerationSlot, SlotAssignment


REROLLS_PER_SLOT = 10


def _week_structure_snapshot(plan, candidates_by_id) -> tuple[int, int, int]:
    composed = 0
    mains = 0
    assigned = 0
    for item in plan.items:
        if item.dish_id is None:
            continue
        assigned += 1
        candidate = candidates_by_id.get(item.dish_id)
        if candidate is None:
            continue
        if candidate_primary_structure(candidate) == MealStructure.composed_pair:
            composed += 1
        else:
            mains += 1
    return composed, mains, assigned


@dataclass(frozen=True)
class MealOutcome:
    kind: str
    label: str
    score: float


def _classify_assignment(assignment: SlotAssignment, names: dict[int, str]) -> MealOutcome:
    lines = assignment.lines
    if len(lines) == 1 and lines[0].role.value == "main":
        dish_id = lines[0].dish_id
        return MealOutcome("main", names.get(dish_id, f"dish#{dish_id}"), assignment.score)
    if len(lines) == 2:
        roles = {line.role.value for line in lines}
        if roles == {"centerpiece", "side"}:
            cp = next(line for line in lines if line.role.value == "centerpiece")
            side = next(line for line in lines if line.role.value == "side")
            cp_name = names.get(cp.dish_id, f"dish#{cp.dish_id}")
            side_name = names.get(side.dish_id, f"dish#{side.dish_id}")
            return MealOutcome("pair", f"{cp_name} + {side_name}", assignment.score)
    return MealOutcome("other", str([(line.role.value, line.dish_id) for line in lines]), assignment.score)


def _describe_current_item(item: MealPlanItem, names: dict[int, str]) -> str:
    if not item.lines and item.dish_id is None:
        return "(empty)"
    if item.lines:
        parts = []
        for line in sorted(item.lines, key=lambda entry: entry.position):
            role = line.role.value
            name = names.get(line.dish_id, f"dish#{line.dish_id}") if line.dish_id else "?"
            parts.append(f"{role}:{name}")
        return " | ".join(parts)
    return names.get(item.dish_id, f"dish#{item.dish_id}")


def _option_kind(option) -> str:
    lines = option.assignment.lines
    if len(lines) == 1 and lines[0].role.value == "main":
        return "main"
    if len(lines) == 2:
        return "pair"
    return "other"


def _analyze_class_pools(main_options, pair_options) -> dict:
    def _top5(options):
        ranked = sorted(options, key=lambda entry: entry.score, reverse=True)
        return ranked[:5]

    main_top5 = _top5(main_options)
    pair_top5 = _top5(pair_options)
    main_scores = [option.score for option in main_options]
    pair_scores = [option.score for option in pair_options]
    return {
        "main_total": len(main_options),
        "pair_total": len(pair_options),
        "main_top5_count": len(main_top5),
        "pair_top5_count": len(pair_top5),
        "best_main_score": max(main_scores) if main_scores else None,
        "best_pair_score": max(pair_scores) if pair_scores else None,
        "main_top5_scores": [round(option.score, 3) for option in main_top5],
        "pair_top5_scores": [round(option.score, 3) for option in pair_top5],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate rerolls per slot (read-only).")
    parser.add_argument("--rerolls", type=int, default=REROLLS_PER_SLOT, help="Rerolls per eligible slot")
    args = parser.parse_args()
    rerolls_per_slot = args.rerolls
    db = SessionLocal()
    try:
        reference_date = household_local_today(db)
        week_start = PlanningService.week_start_for(reference_date)
        rules = PlanningRuleService(db).get_active_rules()
        candidates = load_dish_candidates(db, rules=rules)
        names = {candidate.dish_id: candidate.dish_name for candidate in candidates}

        mains = sum(1 for candidate in candidates if is_main_candidate(candidate))
        centerpieces = sum(1 for candidate in candidates if is_centerpiece_candidate(candidate))
        sides = sum(1 for candidate in candidates if is_side_candidate(candidate))

        plan = db.scalar(
            select(MealPlan)
            .where(MealPlan.week_start_date == week_start)
            .options(selectinload(MealPlan.items).selectinload(MealPlanItem.lines))
        )
        if plan is None:
            print(f"No meal plan for week starting {week_start.isoformat()}")
            return

        print(f"Reference date: {reference_date.isoformat()} (week start {week_start.isoformat()})")
        print(
            f"Catalog: {len(candidates)} candidates "
            f"(mains={mains}, centerpieces={centerpieces}, sides={sides}, "
            f"pair_space={centerpieces * sides})"
        )
        candidates_by_id = {candidate.dish_id: candidate for candidate in candidates}
        print(
            f"Structure policy: composed min={rules.composed_meals_per_week.min} "
            f"max={rules.composed_meals_per_week.max} "
            f"neutral={rules.structure_neutral_share.main:.0%} main / "
            f"{rules.structure_neutral_share.composed_pair:.0%} composed"
        )
        week_composed, week_mains, week_assigned = _week_structure_snapshot(plan, candidates_by_id)
        print(
            f"Current week assignments: {week_assigned} slots "
            f"(composed={week_composed}, mains={week_mains})\n"
        )
        print(f"Simulating {rerolls_per_slot} sequential rerolls per eligible slot (no DB writes)\n")

        items = sorted(plan.items, key=lambda item: (item.date, item.meal_slot.value))

        summary_kinds: Counter[str] = Counter()
        slots_tested = 0

        for item in items:
            slot_label = f"{item.date.isoformat()} {item.meal_slot.value}"
            can_reroll = slot_is_regenerable(
                meal_date=item.date,
                today=reference_date,
                is_locked=item.is_locked,
                manually_selected=item.manually_selected,
                status=item.status,
                planning_state=item.planning_state,
            )
            if not can_reroll:
                print(f"## {slot_label} — SKIPPED (locked/manual/past/do-not-plan)")
                print(f"   Current: {_describe_current_item(item, names)}\n")
                continue

            slots_tested += 1
            slot = GenerationSlot(item_id=item.id, meal_date=item.date, meal_slot=item.meal_slot)

            fixed_assignments: dict[int, int] = {}
            fixed_dates_by_item: dict[int, date] = {}
            for plan_item in plan.items:
                if plan_item.id == item.id or plan_item.dish_id is None:
                    continue
                fixed_assignments[plan_item.id] = plan_item.dish_id
                fixed_dates_by_item[plan_item.id] = plan_item.date

            eaten_meals = load_eaten_meal_snapshots(
                db,
                before_date=item.date + timedelta(days=1),
                window_days=max(rules.history_window_days, rules.avoid_same_dish_within_days),
                rules=rules,
            )

            common = dict(
                slot=slot,
                assigned_dish_ids=[dish_id for dish_id in fixed_assignments.values()],
                forbidden_dish_ids=None,
                forbidden_combination_keys=forbidden_combination_keys(item),
                dish_date_index={},
                neighbours=build_similarity_neighbours(
                    eaten_meals=eaten_meals,
                    fixed_assignments=fixed_assignments,
                    fixed_dates_by_item=fixed_dates_by_item,
                    attempt_assignments=[],
                    slot_dates_by_item={**fixed_dates_by_item, item.id: item.date},
                    candidates_by_id=candidates_by_id,
                    exclude_item_id=item.id,
                ),
                candidates_by_id=candidates_by_id,
                rules=rules,
            )
            main_options = _build_main_options(
                mains=[candidate for candidate in candidates if is_main_candidate(candidate)],
                **common,
            )
            pair_options = _build_pair_options(
                centerpieces=[candidate for candidate in candidates if is_centerpiece_candidate(candidate)],
                sides=[candidate for candidate in candidates if is_side_candidate(candidate)],
                rng=random.Random(0),
                **common,
            )
            pool = _analyze_class_pools(main_options, pair_options)

            other_fixed = dict(fixed_assignments)
            composed_in_week, mains_in_week = count_week_structures(
                fixed_assignments=other_fixed,
                attempt_assignments=[],
                candidates_by_id=candidates_by_id,
            )
            preferred, _, pref_codes = select_preferred_structure(
                composed_in_week,
                rules=rules,
                rng=random.Random(0),
            )

            print(f"## {slot_label}")
            print(f"   Current: {_describe_current_item(item, names)}")
            print(
                f"   Week context (excluding this slot): composed={composed_in_week}, mains={mains_in_week} "
                f"→ preferred={preferred.value} ({', '.join(pref_codes) or 'neutral'})"
            )
            print(
                f"   Class pools: mains={pool['main_total']}, pairs={pool['pair_total']} "
                f"(best scores main={pool['best_main_score']}, pair={pool['best_pair_score']})"
            )
            print(f"   Main top-5 scores: {pool['main_top5_scores']}")
            print(f"   Pair top-5 scores: {pool['pair_top5_scores']}")

            excluded = forbidden_combination_keys(item)
            slot_kinds: Counter[str] = Counter()
            exhausted_at: int | None = None

            for attempt in range(1, rerolls_per_slot + 1):
                result = generate_week_assignments(
                    [slot],
                    candidates,
                    fixed_assignments=fixed_assignments,
                    fixed_dates_by_item=fixed_dates_by_item,
                    eaten_meals=eaten_meals,
                    rules=rules,
                    today=reference_date,
                    forbidden_combination_keys=excluded,
                )
                if not result.assignments:
                    exhausted_at = attempt
                    print(f"   Reroll {attempt:2d}: EXHAUSTED (no alternatives left)")
                    break

                assignment = result.assignments[0]
                outcome = _classify_assignment(assignment, names)
                slot_kinds[outcome.kind] += 1
                summary_kinds[outcome.kind] += 1
                if attempt <= 5 or attempt % 20 == 0 or attempt == rerolls_per_slot:
                    print(f"   Reroll {attempt:3d}: [{outcome.kind:5s}] score={outcome.score:.3f} — {outcome.label}")

                key = combination_key_from_assignment(assignment)
                excluded = excluded | {key}

            if exhausted_at is None:
                unique = len(excluded) - len(forbidden_combination_keys(item))
                print(f"   After {rerolls_per_slot} rerolls: {dict(slot_kinds)} ({unique} unique new combinations)")
            else:
                print(f"   Exhausted on reroll {exhausted_at}; outcomes before exhaustion: {dict(slot_kinds)}")
            print()

        print("=== Summary ===")
        print(f"Slots tested: {slots_tested}")
        print(f"All reroll outcomes: {dict(summary_kinds)}")
        if summary_kinds:
            total = sum(summary_kinds.values())
            mains_pct = 100.0 * summary_kinds.get("main", 0) / total
            pairs_pct = 100.0 * summary_kinds.get("pair", 0) / total
            print(f"Mains: {summary_kinds.get('main', 0)}/{total} ({mains_pct:.1f}%)")
            print(f"Pairs: {summary_kinds.get('pair', 0)}/{total} ({pairs_pct:.1f}%)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
