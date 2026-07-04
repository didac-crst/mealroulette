from __future__ import annotations

from datetime import date, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, selectinload

from mealroulette.models.planning import MealPlan, MealPlanItem
from mealroulette.services.planning import PlanningService
from mealroulette.services.planning_rule_service import PlanningRuleService
from mealroulette.services.scheduler.catalog import load_dish_candidates, load_eaten_meal_snapshots
from mealroulette.services.scheduler.constraints import slot_is_regenerable
from mealroulette.services.scheduler.generator import generate_week_assignments
from mealroulette.services.scheduler.types import GenerationSlot, WeekGenerationResult
from mealroulette.services.scheduler.variety import build_variety_assessment


class SchedulerService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.rules_service = PlanningRuleService(db)
        self.planning_service = PlanningService(db)

    def generate_week(
        self,
        meal_plan_id: int,
        *,
        today: date | None = None,
    ) -> tuple[WeekGenerationResult, dict]:
        reference_date = today or date.today()
        rules = self.rules_service.get_active_rules()
        plan = self._load_plan(meal_plan_id)

        candidates = load_dish_candidates(self.db, rules=rules)
        if not candidates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active dishes available for scheduling",
            )

        regenerable_slots: list[GenerationSlot] = []
        fixed_assignments: dict[int, int] = {}
        fixed_dates_by_item: dict[int, date] = {}

        for item in plan.items:
            if slot_is_regenerable(
                meal_date=item.date,
                today=reference_date,
                is_locked=item.is_locked,
                manually_selected=item.manually_selected,
                status=item.status,
            ):
                regenerable_slots.append(
                    GenerationSlot(item_id=item.id, meal_date=item.date, meal_slot=item.meal_slot)
                )
            elif item.dish_id is not None:
                fixed_assignments[item.id] = item.dish_id
                fixed_dates_by_item[item.id] = item.date

        if not regenerable_slots:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No eligible meal slots to regenerate",
            )

        latest_slot_date = max(slot.meal_date for slot in regenerable_slots)
        eaten_meals = load_eaten_meal_snapshots(
            self.db,
            before_date=latest_slot_date + timedelta(days=1),
            window_days=max(rules.history_window_days, rules.avoid_same_dish_within_days),
            rules=rules,
        )

        result = generate_week_assignments(
            regenerable_slots,
            candidates,
            fixed_assignments=fixed_assignments,
            fixed_dates_by_item=fixed_dates_by_item,
            eaten_meals=eaten_meals,
            rules=rules,
            today=reference_date,
        )

        if not result.assignments:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.warnings[0])

        candidates_by_id = {candidate.dish_id: candidate for candidate in candidates}
        variety = build_variety_assessment(
            new_assignments=[
                (
                    assignment.dish_id,
                    candidates_by_id[assignment.dish_id].dish_name,
                    candidates_by_id[assignment.dish_id].vector,
                )
                for assignment in result.assignments
            ],
            recent_meals=eaten_meals,
        )

        self._apply_assignments(result)
        return result, variety

    def _load_plan(self, meal_plan_id: int) -> MealPlan:
        plan = self.db.get(
            MealPlan,
            meal_plan_id,
            options=(selectinload(MealPlan.items),),
        )
        if plan is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal plan not found")
        return plan

    def _apply_assignments(self, result: WeekGenerationResult) -> None:
        for assignment in result.assignments:
            item = self.db.get(MealPlanItem, assignment.item_id)
            if item is None:
                continue
            item.dish_id = assignment.dish_id
            item.recipe_id = assignment.recipe_id
            item.manually_selected = False
            item.selection_reasons_json = assignment.selection_reasons_json
        self.db.commit()
