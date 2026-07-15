#!/usr/bin/env python3
"""Manual dev benchmark for week generation against the local database."""

from __future__ import annotations

import time
from datetime import date

from mealroulette.models.household import DEFAULT_HOUSEHOLD_ID
from mealroulette.db.session import SessionLocal
from mealroulette.services.planning import PlanningService
from mealroulette.services.planning_rule_service import PlanningRuleService
from mealroulette.services.scheduler.catalog import load_dish_candidates
from mealroulette.services.scheduler.composition import is_centerpiece_candidate, is_side_candidate
from mealroulette.services.scheduler.generator import _effective_plan_attempts
from mealroulette.services.scheduler_service import SchedulerService


def main() -> None:
    db = SessionLocal()
    try:
        rules = PlanningRuleService(db, household_id=DEFAULT_HOUSEHOLD_ID).get_active_rules()
        started = time.perf_counter()
        candidates = load_dish_candidates(db, rules=rules, household_id=DEFAULT_HOUSEHOLD_ID)
        load_seconds = time.perf_counter() - started

        centerpiece_count = sum(1 for candidate in candidates if is_centerpiece_candidate(candidate))
        side_count = sum(1 for candidate in candidates if is_side_candidate(candidate))
        effective_attempts = _effective_plan_attempts(rules, candidates)

        planning = PlanningService(db, DEFAULT_HOUSEHOLD_ID)
        plan = planning.get_or_create_plan(date.today())
        svc = SchedulerService(db, DEFAULT_HOUSEHOLD_ID)

        started = time.perf_counter()
        svc.generate_week(plan.id, today=date.today())
        generate_seconds = time.perf_counter() - started

        print(f"candidates={len(candidates)} centerpieces={centerpiece_count} sides={side_count}")
        print(f"pair_space={centerpiece_count * side_count}")
        print(f"plan_attempts configured={rules.plan_attempts} effective={effective_attempts}")
        print(f"load_candidates={load_seconds:.2f}s generate_week={generate_seconds:.2f}s")
    finally:
        db.close()


if __name__ == "__main__":
    main()
