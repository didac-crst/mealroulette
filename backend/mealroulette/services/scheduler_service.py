from __future__ import annotations

from datetime import date, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from mealroulette.models.planning import MealPlan, MealPlanItem
from mealroulette.services.household_time import household_local_today
from mealroulette.services.meal_plan_lines import sync_legacy_mirror
from mealroulette.services.planning import PlanningService
from mealroulette.services.planning_rule_service import PlanningRuleService
from mealroulette.services.scheduler.catalog import load_dish_candidates, load_eaten_meal_snapshots
from mealroulette.services.scheduler.composition import item_has_roulette_lines, roulette_dish_ids
from mealroulette.services.scheduler.constraints import slot_is_regenerable
from mealroulette.services.scheduler.generator import generate_week_assignments
from mealroulette.services.scheduler.neighbours import build_similarity_neighbours
from mealroulette.services.scheduler.types import GenerationSlot, WeekGenerationResult
from mealroulette.services.scheduler.undo import clear_undo_snapshot, restore_undo_snapshot, save_undo_snapshot
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
        reference_date = today or household_local_today(self.db)
        rules = self.rules_service.get_active_rules()
        plan = self._load_plan_for_update(meal_plan_id)
        candidates = self._load_candidates(rules)

        regenerable_slots, fixed_assignments, fixed_dates_by_item = self._partition_plan_items(
            plan,
            reference_date=reference_date,
        )
        if not regenerable_slots:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No eligible meal slots to regenerate",
            )

        eaten_meals = self._load_eaten_meals(regenerable_slots, rules)
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

        variety = self._build_variety(
            result,
            candidates,
            eaten_meals,
            fixed_assignments,
            fixed_dates_by_item,
            plan,
        )
        undo_items = [item for item in plan.items if item.id in {slot.item_id for slot in regenerable_slots}]
        save_undo_snapshot(plan, action="generate_week", items=undo_items)
        self._apply_assignments(result)
        return result, variety

    def reroll_item(
        self,
        item_id: int,
        *,
        today: date | None = None,
    ) -> tuple[WeekGenerationResult, dict]:
        reference_date = today or household_local_today(self.db)
        rules = self.rules_service.get_active_rules()
        item = self._load_item(item_id)
        if not self._slot_can_reroll(item, reference_date=reference_date):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This meal slot cannot be rerolled",
            )

        previous_roulette_dish_ids = roulette_dish_ids(item)
        plan = self._load_plan_for_update(item.meal_plan_id)
        item = next(plan_item for plan_item in plan.items if plan_item.id == item_id)
        candidates = self._load_candidates(rules)
        slot = GenerationSlot(item_id=item.id, meal_date=item.date, meal_slot=item.meal_slot)

        fixed_assignments: dict[int, int] = {}
        fixed_dates_by_item: dict[int, date] = {}
        for plan_item in plan.items:
            if plan_item.id == item.id or plan_item.dish_id is None:
                continue
            fixed_assignments[plan_item.id] = plan_item.dish_id
            fixed_dates_by_item[plan_item.id] = plan_item.date

        forbidden_dish_ids = frozenset(previous_roulette_dish_ids) if previous_roulette_dish_ids else None
        eaten_meals = self._load_eaten_meals([slot], rules)
        result = generate_week_assignments(
            [slot],
            candidates,
            fixed_assignments=fixed_assignments,
            fixed_dates_by_item=fixed_dates_by_item,
            eaten_meals=eaten_meals,
            rules=rules,
            today=reference_date,
            forbidden_dish_ids=forbidden_dish_ids,
        )
        if not result.assignments:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.warnings[0])

        variety = self._build_variety(
            result,
            candidates,
            eaten_meals,
            fixed_assignments,
            fixed_dates_by_item,
            plan,
        )
        save_undo_snapshot(plan, action="reroll", items=[item])
        self._apply_assignments(result)
        return result, variety

    def undo_last_roulette(self, meal_plan_id: int) -> bool:
        plan = self._load_plan(meal_plan_id)
        if plan.last_roulette_undo_json is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No roulette action to undo",
            )
        restored = restore_undo_snapshot(self.db, plan)
        self.db.commit()
        return restored

    def has_undo(self, meal_plan_id: int) -> bool:
        plan = self._load_plan(meal_plan_id)
        return plan.last_roulette_undo_json is not None

    def _slot_can_reroll(self, item: MealPlanItem, *, reference_date: date) -> bool:
        if not slot_is_regenerable(
            meal_date=item.date,
            today=reference_date,
            is_locked=item.is_locked,
            manually_selected=item.manually_selected,
            status=item.status,
            planning_state=item.planning_state,
        ):
            return False
        return item_has_roulette_lines(item) or not item.lines

    def _load_candidates(self, rules):
        candidates = load_dish_candidates(self.db, rules=rules)
        if not candidates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active dishes available for scheduling",
            )
        return candidates

    def _partition_plan_items(
        self,
        plan: MealPlan,
        *,
        reference_date: date,
    ) -> tuple[list[GenerationSlot], dict[int, int], dict[int, date]]:
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
                planning_state=item.planning_state,
            ):
                regenerable_slots.append(
                    GenerationSlot(item_id=item.id, meal_date=item.date, meal_slot=item.meal_slot)
                )
            elif item.dish_id is not None:
                fixed_assignments[item.id] = item.dish_id
                fixed_dates_by_item[item.id] = item.date

        return regenerable_slots, fixed_assignments, fixed_dates_by_item

    def _load_eaten_meals(self, slots, rules):
        latest_slot_date = max(slot.meal_date for slot in slots)
        return load_eaten_meal_snapshots(
            self.db,
            before_date=latest_slot_date + timedelta(days=1),
            window_days=max(rules.history_window_days, rules.avoid_same_dish_within_days),
            rules=rules,
        )

    def _build_variety(self, result, candidates, eaten_meals, fixed_assignments, fixed_dates_by_item, plan):
        candidates_by_id = {candidate.dish_id: candidate for candidate in candidates}
        item_dates = {item.id: item.date for item in plan.items}
        slot_dates_by_item = dict(fixed_dates_by_item)
        for assignment in result.assignments:
            slot_dates_by_item[assignment.item_id] = item_dates[assignment.item_id]
        neighbours = build_similarity_neighbours(
            eaten_meals=eaten_meals,
            fixed_assignments=fixed_assignments,
            fixed_dates_by_item=fixed_dates_by_item,
            attempt_assignments=result.assignments,
            slot_dates_by_item=slot_dates_by_item,
            candidates_by_id=candidates_by_id,
        )
        return build_variety_assessment(
            new_assignments=[
                (
                    assignment.item_id,
                    assignment.dish_id,
                    candidates_by_id[assignment.dish_id].dish_name,
                    candidates_by_id[assignment.dish_id].vector,
                )
                for assignment in result.assignments
            ],
            neighbours=neighbours,
        )

    def _load_plan_for_update(self, meal_plan_id: int) -> MealPlan:
        plan = self.db.scalar(
            select(MealPlan)
            .where(MealPlan.id == meal_plan_id)
            .options(selectinload(MealPlan.items).selectinload(MealPlanItem.lines))
            .with_for_update()
        )
        if plan is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal plan not found")
        return plan

    def _load_plan(self, meal_plan_id: int) -> MealPlan:
        plan = self.db.get(
            MealPlan,
            meal_plan_id,
            options=(selectinload(MealPlan.items).selectinload(MealPlanItem.lines),),
        )
        if plan is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal plan not found")
        return plan

    def _load_item(self, item_id: int) -> MealPlanItem:
        item = self.db.scalar(
            select(MealPlanItem)
            .where(MealPlanItem.id == item_id)
            .options(selectinload(MealPlanItem.lines))
        )
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal plan item not found")
        return item

    def _apply_assignments(self, result: WeekGenerationResult) -> None:
        for assignment in result.assignments:
            self.planning_service.apply_roulette_package(assignment.item_id, assignment)
        self.db.commit()
