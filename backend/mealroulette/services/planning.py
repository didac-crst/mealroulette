from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from mealroulette.models.catalog import Dish, Recipe
from mealroulette.models.enums import (
    MealPlanDishLineRole,
    MealPlanDishLineSource,
    MealPlanItemStatus,
    MealPlanningState,
    MealPlanStatus,
    MealSlot,
)
from mealroulette.models.planning import MealPlan, MealPlanItem, MealPlanItemDish, MealRating
from mealroulette.services.household_time import household_local_today
from mealroulette.services.meal_plan_lines import (
    compute_meal_title,
    role_for_dish,
    sync_legacy_mirror,
)
from mealroulette.services.scheduler.undo import clear_undo_snapshot
from mealroulette.services.recipe_traits import (
    RECIPE_TRAIT_INGREDIENT_LOAD,
    compute_recipe_traits_now,
    effective_traits_for_meal_slot,
)
from mealroulette.services.scheduler.catalog import load_reference_units
from mealroulette.schemas.planning import (
    MealPlanCreateRequest,
    MealPlanDishLineCreateRequest,
    MealPlanDishLinePublic,
    MealPlanDishLineUpdateRequest,
    MealPlanDoNotPlanRequest,
    MealPlanItemPublic,
    MealPlanItemUpdateRequest,
    MealPlanPublic,
    MealRatingCreateRequest,
    MealRatingPublic,
    MealRatingUpsertResponse,
)
from mealroulette.services.planning_rules import (
    _EATEN_STATUSES,
    is_future_meal_date,
    is_leftover_source_candidate,
    is_valid_leftover_source_status,
    is_within_leftover_window,
    meal_slot_sort_key,
)


class PlanningService:
    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def _meal_plan_item_trait_options() -> tuple:
        line_recipe_load = (
            selectinload(MealPlanItem.lines)
            .selectinload(MealPlanItemDish.recipe)
            .options(*RECIPE_TRAIT_INGREDIENT_LOAD),
            selectinload(MealPlanItem.lines).selectinload(MealPlanItemDish.dish),
        )
        return (
            selectinload(MealPlanItem.recipe).options(*RECIPE_TRAIT_INGREDIENT_LOAD),
            selectinload(MealPlanItem.dish)
            .selectinload(Dish.recipes)
            .options(*RECIPE_TRAIT_INGREDIENT_LOAD),
            *line_recipe_load,
        )

    @staticmethod
    def week_start_for(date_value: date) -> date:
        return date_value - timedelta(days=date_value.weekday())

    @staticmethod
    def _meal_times(item: MealPlanItem) -> tuple[int | None, int | None]:
        prep = item.recipe.prep_time_minutes if item.recipe is not None else None
        cook = item.recipe.cook_time_minutes if item.recipe is not None else None
        if item.dish is not None:
            prep = prep if prep is not None else item.dish.default_prep_time_minutes
            cook = cook if cook is not None else item.dish.default_cook_time_minutes
        return prep, cook

    def _to_line_public(
        self,
        line: MealPlanItemDish,
        *,
        gram_unit=None,
        ml_unit=None,
    ) -> MealPlanDishLinePublic:
        traits = None
        if line.recipe is not None:
            traits = compute_recipe_traits_now(self.db, line.recipe, gram_unit=gram_unit, ml_unit=ml_unit)
        return MealPlanDishLinePublic(
            id=line.id,
            meal_plan_item_id=line.meal_plan_item_id,
            dish_id=line.dish_id,
            recipe_id=line.recipe_id,
            dish_name=line.dish.name if line.dish else None,
            recipe_variant_name=line.recipe.variant_name if line.recipe else None,
            role=line.role,
            source=line.source,
            position=line.position,
            selection_reasons_json=line.selection_reasons_json,
            computed_traits_json=traits,
        )

    def to_item_public(
        self,
        item: MealPlanItem,
        *,
        gram_unit=None,
        ml_unit=None,
    ) -> MealPlanItemPublic:
        prep_time_minutes, cook_time_minutes = self._meal_times(item)
        lines = sorted(item.lines, key=lambda line: line.position)
        line_publics = [
            self._to_line_public(line, gram_unit=gram_unit, ml_unit=ml_unit) for line in lines
        ]
        return MealPlanItemPublic(
            id=item.id,
            meal_plan_id=item.meal_plan_id,
            date=item.date,
            meal_slot=item.meal_slot,
            dish_id=item.dish_id,
            recipe_id=item.recipe_id,
            dish_name=item.dish.name if item.dish else None,
            recipe_variant_name=item.recipe.variant_name if item.recipe else None,
            prep_time_minutes=prep_time_minutes,
            cook_time_minutes=cook_time_minutes,
            status=item.status,
            planning_state=item.planning_state,
            title=compute_meal_title(item, lines),
            lines=line_publics,
            is_locked=item.is_locked,
            manually_selected=item.manually_selected,
            skip_reason=item.skip_reason,
            skip_comment=item.skip_comment,
            leftover_source_item_id=item.leftover_source_item_id,
            selection_reasons_json=item.selection_reasons_json,
            computed_traits_json=effective_traits_for_meal_slot(
                db=self.db,
                lines=lines,
                recipe=item.recipe,
                dish_recipes=item.dish.recipes if item.dish is not None else None,
                gram_unit=gram_unit,
                ml_unit=ml_unit,
            ),
            review_saved_at=item.review_saved_at,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    def to_plan_public(self, plan: MealPlan) -> MealPlanPublic:
        gram_unit, ml_unit = load_reference_units(self.db)
        items = sorted(plan.items, key=lambda item: (item.date, meal_slot_sort_key(item.meal_slot)))
        return MealPlanPublic(
            id=plan.id,
            week_start_date=plan.week_start_date,
            status=plan.status,
            items=[self.to_item_public(item, gram_unit=gram_unit, ml_unit=ml_unit) for item in items],
            roulette_undo_available=plan.last_roulette_undo_json is not None,
            created_at=plan.created_at,
            updated_at=plan.updated_at,
        )

    def _load_plan(self, plan_id: int) -> MealPlan:
        plan = self.db.scalar(
            select(MealPlan)
            .where(MealPlan.id == plan_id)
            .options(
                selectinload(MealPlan.items).options(*self._meal_plan_item_trait_options()),
            )
        )
        if plan is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal plan not found")
        return plan

    def _load_item(self, item_id: int) -> MealPlanItem:
        item = self.db.scalar(
            select(MealPlanItem)
            .where(MealPlanItem.id == item_id)
            .options(
                *self._meal_plan_item_trait_options(),
                selectinload(MealPlanItem.meal_rating),
            )
        )
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal plan item not found")
        return item

    def _assert_can_execute(self, item: MealPlanItem) -> None:
        if is_future_meal_date(item.date):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change meal status for a future date",
            )

    def _assert_assignment_allowed(self, item: MealPlanItem) -> None:
        if item.is_locked:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change dish or recipe on a locked meal",
            )

    def _scaffold_items(self, plan: MealPlan, week_start: date) -> None:
        for day_offset in range(7):
            item_date = week_start + timedelta(days=day_offset)
            for meal_slot in (MealSlot.lunch, MealSlot.dinner):
                self.db.add(
                    MealPlanItem(
                        meal_plan=plan,
                        date=item_date,
                        meal_slot=meal_slot,
                        status=MealPlanItemStatus.planned,
                    )
                )

    def _load_plan_by_week_start(self, week_start: date) -> MealPlan | None:
        return self.db.scalar(
            select(MealPlan)
            .where(MealPlan.week_start_date == week_start)
            .options(
                selectinload(MealPlan.items).options(*self._meal_plan_item_trait_options()),
            )
        )

    def get_or_create_plan(self, week_start: date, *, status: MealPlanStatus = MealPlanStatus.active) -> MealPlan:
        normalized = self.week_start_for(week_start)
        plan = self._load_plan_by_week_start(normalized)
        if plan is not None:
            return plan

        plan = MealPlan(week_start_date=normalized, status=status)
        self.db.add(plan)
        self.db.flush()
        self._scaffold_items(plan, normalized)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            existing = self._load_plan_by_week_start(normalized)
            if existing is None:
                raise
            return existing
        return self._load_plan(plan.id)

    def get_current_plan(self) -> MealPlanPublic:
        plan = self.get_or_create_plan(household_local_today(self.db))
        return self.to_plan_public(plan)

    def get_plan_by_week(self, week_start: date) -> MealPlanPublic:
        plan = self.get_or_create_plan(week_start)
        return self.to_plan_public(plan)

    def create_plan(self, payload: MealPlanCreateRequest) -> MealPlanPublic:
        normalized = self.week_start_for(payload.week_start_date)
        existing = self.db.scalar(select(MealPlan).where(MealPlan.week_start_date == normalized))
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Meal plan for this week already exists")
        plan = MealPlan(week_start_date=normalized, status=payload.status)
        self.db.add(plan)
        self.db.flush()
        self._scaffold_items(plan, normalized)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Meal plan for this week already exists",
            ) from None
        return self.to_plan_public(self._load_plan(plan.id))

    def _resolve_recipe_for_dish(self, dish_id: int, recipe_id: int | None) -> int | None:
        if recipe_id is not None:
            recipe = self.db.get(Recipe, recipe_id)
            if recipe is None or recipe.dish_id != dish_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Recipe does not belong to dish")
            return recipe.id
        main_recipe = self.db.scalar(
            select(Recipe).where(Recipe.dish_id == dish_id, Recipe.is_main.is_(True))
        )
        if main_recipe is None:
            main_recipe = self.db.scalar(
                select(Recipe).where(Recipe.dish_id == dish_id).order_by(Recipe.id).limit(1)
            )
        return main_recipe.id if main_recipe else None

    def _assert_slot_mutable(self, item: MealPlanItem) -> None:
        if item.planning_state == MealPlanningState.do_not_plan:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot modify a do-not-plan meal slot",
            )

    def _next_line_position(self, item: MealPlanItem) -> int:
        if not item.lines:
            return 0
        return max(line.position for line in item.lines) + 1

    def _resolve_line_position(self, item: MealPlanItem, position: int | None, *, exclude_line_id: int | None = None) -> int:
        if position is None:
            return self._next_line_position(item)
        occupied = {
            line.position
            for line in item.lines
            if exclude_line_id is None or line.id != exclude_line_id
        }
        if position in occupied:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Line position {position} is already occupied",
            )
        return position

    def _append_manual_line(
        self,
        item: MealPlanItem,
        dish_id: int,
        recipe_id: int | None,
        *,
        role: MealPlanDishLineRole | None = None,
        position: int | None = None,
    ) -> MealPlanItemDish:
        dish = self.db.get(Dish, dish_id)
        if dish is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dish not found")
        resolved_recipe_id = self._resolve_recipe_for_dish(dish_id, recipe_id)
        resolved_position = self._resolve_line_position(item, position)
        line = MealPlanItemDish(
            meal_plan_item_id=item.id,
            dish_id=dish_id,
            recipe_id=resolved_recipe_id,
            position=resolved_position,
            role=role or role_for_dish(dish),
            source=MealPlanDishLineSource.manual,
            selection_reasons_json=None,
        )
        item.lines.append(line)
        sync_legacy_mirror(item)
        return line

    def _clear_all_lines(self, item: MealPlanItem) -> None:
        item.lines.clear()
        sync_legacy_mirror(item)

    def _remove_roulette_lines(self, item: MealPlanItem) -> None:
        self.db.execute(
            delete(MealPlanItemDish).where(
                MealPlanItemDish.meal_plan_item_id == item.id,
                MealPlanItemDish.source == MealPlanDishLineSource.roulette,
            )
        )
        self.db.flush()
        self.db.expire(item, ["lines"])
        for index, line in enumerate(sorted(item.lines, key=lambda row: row.position)):
            line.position = index
        sync_legacy_mirror(item)

    def apply_roulette_package(self, item_id: int, assignment) -> None:
        item = self._load_item(item_id)
        manual_snapshot = [
            (
                line.dish_id,
                line.recipe_id,
                line.role,
                line.selection_reasons_json,
            )
            for line in sorted(item.lines, key=lambda row: row.position)
            if line.source == MealPlanDishLineSource.manual
        ]
        self.db.execute(delete(MealPlanItemDish).where(MealPlanItemDish.meal_plan_item_id == item.id))
        self.db.flush()
        item.lines.clear()
        for index, (dish_id, recipe_id, role, reasons) in enumerate(manual_snapshot):
            item.lines.append(
                MealPlanItemDish(
                    meal_plan_item_id=item.id,
                    dish_id=dish_id,
                    recipe_id=recipe_id,
                    position=index,
                    role=role,
                    source=MealPlanDishLineSource.manual,
                    selection_reasons_json=reasons,
                )
            )
        next_position = len(manual_snapshot)
        for offset, line_def in enumerate(assignment.lines):
            item.lines.append(
                MealPlanItemDish(
                    meal_plan_item_id=item.id,
                    dish_id=line_def.dish_id,
                    recipe_id=line_def.recipe_id,
                    position=next_position + offset,
                    role=line_def.role,
                    source=MealPlanDishLineSource.roulette,
                    selection_reasons_json=line_def.selection_reasons_json,
                )
            )
        sync_legacy_mirror(item)

    def _apply_assignment(
        self,
        item: MealPlanItem,
        dish_id: int | None,
        recipe_id: int | None,
        *,
        mode: str = "replace_all",
    ) -> None:
        self._assert_slot_mutable(item)
        if dish_id is None:
            if item.status != MealPlanItemStatus.planned:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot clear dish on a meal that has already been reviewed",
                )
            self._clear_all_lines(item)
            return

        if mode == "add":
            self._append_manual_line(item, dish_id, recipe_id)
        elif mode == "replace_roulette":
            self._remove_roulette_lines(item)
            self._append_manual_line(item, dish_id, recipe_id)
        else:
            self._clear_all_lines(item)
            self._append_manual_line(item, dish_id, recipe_id, position=0)

        if item.status == MealPlanItemStatus.skipped:
            item.status = MealPlanItemStatus.planned
        item.skip_reason = None
        item.skip_comment = None
        item.leftover_source_item_id = None

    def update_item(self, item_id: int, payload: MealPlanItemUpdateRequest) -> MealPlanItemPublic:
        item = self._load_item(item_id)
        updates = payload.model_dump(exclude_unset=True)
        forbidden_fields = {"status", "is_locked", "skip_reason", "skip_comment"}
        blocked = forbidden_fields.intersection(updates)
        if blocked:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot update {', '.join(sorted(blocked))} via this endpoint",
            )
        if "dish_id" in updates or "recipe_id" in updates:
            self._assert_assignment_allowed(item)
            dish_id = updates.get("dish_id", item.dish_id)
            if "recipe_id" in updates:
                recipe_id = updates["recipe_id"]
            elif "dish_id" in updates:
                recipe_id = None
            else:
                recipe_id = item.recipe_id
            if dish_id is None and recipe_id is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="recipe_id requires dish_id",
                )
            self._apply_assignment(item, dish_id, recipe_id if dish_id is not None else None)
            updates.pop("dish_id", None)
            updates.pop("recipe_id", None)
        if "leftover_source_item_id" in updates:
            if item.status != MealPlanItemStatus.ate_leftovers:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="leftover_source_item_id is only valid for ate_leftovers meals",
                )
            source_id = updates["leftover_source_item_id"]
            if source_id is not None:
                self._validate_leftover_source(item, source_id)
                source = self.db.get(MealPlanItem, source_id)
                item.dish_id = source.dish_id
                item.recipe_id = source.recipe_id
                item.manually_selected = True
            item.review_saved_at = datetime.now(timezone.utc)
        for field, value in updates.items():
            if field == "leftover_source_item_id":
                setattr(item, field, updates["leftover_source_item_id"])
                continue
            setattr(item, field, value)
        self.db.commit()
        self.db.refresh(item)
        return self.to_item_public(self._load_item(item.id))

    def _validate_leftover_source(self, item: MealPlanItem, source_id: int) -> None:
        if source_id == item.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A meal cannot be its own leftover source",
            )
        source = self.db.get(MealPlanItem, source_id)
        if source is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leftover source meal not found")
        if not is_leftover_source_candidate(
            source_id=source.id,
            source_date=source.date,
            source_status=source.status,
            item_id=item.id,
            item_date=item.date,
        ):
            if not is_valid_leftover_source_status(source.status):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Leftover source must be a meal with status eaten",
                )
            if not is_within_leftover_window(source.date, item.date):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Leftover source must be within the last 7 days",
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid leftover source meal",
            )

    def mark_eaten(self, item_id: int) -> MealPlanItemPublic:
        item = self._load_item(item_id)
        self._assert_can_execute(item)
        if item.dish_id is None and not item.lines:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assign a dish before marking the meal as eaten",
            )
        item.status = MealPlanItemStatus.eaten
        item.skip_reason = None
        item.skip_comment = None
        item.leftover_source_item_id = None
        item.review_saved_at = None
        self.db.commit()
        return self.to_item_public(self._load_item(item.id))

    def skip_item(
        self,
        item_id: int,
        skip_reason: str | None,
        skip_comment: str | None,
    ) -> MealPlanItemPublic:
        item = self._load_item(item_id)
        self._assert_can_execute(item)
        item.status = MealPlanItemStatus.skipped
        item.skip_reason = skip_reason
        item.skip_comment = skip_comment
        item.leftover_source_item_id = None
        item.review_saved_at = datetime.now(timezone.utc)
        self.db.commit()
        return self.to_item_public(self._load_item(item.id))

    def mark_ate_leftovers(self, item_id: int, leftover_source_item_id: int | None) -> MealPlanItemPublic:
        item = self._load_item(item_id)
        self._assert_can_execute(item)
        if leftover_source_item_id is not None:
            self._validate_leftover_source(item, leftover_source_item_id)
            source = self.db.get(MealPlanItem, leftover_source_item_id)
            item.dish_id = source.dish_id
            item.recipe_id = source.recipe_id
            item.manually_selected = True
        item.status = MealPlanItemStatus.ate_leftovers
        item.leftover_source_item_id = leftover_source_item_id
        item.skip_reason = None
        item.skip_comment = None
        item.review_saved_at = None
        self.db.commit()
        return self.to_item_public(self._load_item(item.id))

    def lock_item(self, item_id: int) -> MealPlanItemPublic:
        item = self._load_item(item_id)
        if not item.lines and item.dish_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assign a dish before locking the meal",
            )
        item.is_locked = True
        plan = self.db.get(MealPlan, item.meal_plan_id)
        if plan is not None:
            clear_undo_snapshot(plan)
        self.db.commit()
        return self.to_item_public(self._load_item(item.id))

    def unlock_item(self, item_id: int) -> MealPlanItemPublic:
        item = self._load_item(item_id)
        item.is_locked = False
        self.db.commit()
        return self.to_item_public(self._load_item(item.id))

    def reset_status_to_planned(self, item_id: int) -> MealPlanItemPublic:
        item = self._load_item(item_id)
        if item.status == MealPlanItemStatus.planned:
            return self.to_item_public(item)
        self._assert_can_execute(item)
        item.status = MealPlanItemStatus.planned
        item.leftover_source_item_id = None
        item.skip_reason = None
        item.skip_comment = None
        item.review_saved_at = None
        rating = self.db.scalar(select(MealRating).where(MealRating.meal_plan_item_id == item.id))
        if rating is not None:
            self.db.delete(rating)
        self.db.commit()
        return self.to_item_public(self._load_item(item.id))

    def get_meal_rating(self, item_id: int) -> MealRatingPublic | None:
        item = self._load_item(item_id)
        if item.meal_rating is None:
            rating = self.db.scalar(select(MealRating).where(MealRating.meal_plan_item_id == item.id))
            if rating is None:
                return None
            return MealRatingPublic.model_validate(rating)
        return MealRatingPublic.model_validate(item.meal_rating)

    def upsert_meal_rating(self, item_id: int, payload: MealRatingCreateRequest) -> MealRatingUpsertResponse:
        item = self._load_item(item_id)
        self._assert_can_execute(item)
        if item.status not in _EATEN_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only rate meals that were eaten",
            )
        if item.dish_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot rate a meal without a dish",
            )
        rating = self.db.scalar(select(MealRating).where(MealRating.meal_plan_item_id == item.id))
        if rating is None:
            rating = MealRating(
                meal_plan_item_id=item.id,
                dish_id=item.dish_id,
                recipe_id=item.recipe_id,
                rating=payload.rating,
                comment=payload.comment,
            )
            self.db.add(rating)
        else:
            rating.dish_id = item.dish_id
            rating.recipe_id = item.recipe_id
            rating.rating = payload.rating
            rating.comment = payload.comment
        item.review_saved_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(rating)
        return MealRatingUpsertResponse(
            rating=MealRatingPublic.model_validate(rating),
            item=self.to_item_public(self._load_item(item.id)),
        )

    def list_history(self, *, limit: int = 50) -> list[MealPlanItemPublic]:
        gram_unit, ml_unit = load_reference_units(self.db)
        items = self.db.scalars(
            select(MealPlanItem)
            .where(
                MealPlanItem.status.in_(
                    [
                        MealPlanItemStatus.eaten,
                        MealPlanItemStatus.skipped,
                        MealPlanItemStatus.ate_leftovers,
                    ]
                )
            )
            .options(*self._meal_plan_item_trait_options())
            .order_by(MealPlanItem.date.desc(), MealPlanItem.meal_slot.desc())
            .limit(limit)
        )
        return [self.to_item_public(item, gram_unit=gram_unit, ml_unit=ml_unit) for item in items]

    def swap_items(self, source_item_id: int, target_item_id: int) -> tuple[MealPlanItemPublic, MealPlanItemPublic]:
        source = self._load_item(source_item_id)
        target = self._load_item(target_item_id)
        if source.meal_plan_id != target.meal_plan_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Meals must belong to the same week plan",
            )
        if source.id == target.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot swap a meal with itself",
            )

        reference_date = household_local_today(self.db)
        for item in (source, target):
            if item.is_locked:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot swap locked meals",
                )
            if item.status != MealPlanItemStatus.planned:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Can only swap planned meals",
                )
            if item.date < reference_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot swap past meals",
                )

        source_dish_id = source.dish_id
        source_recipe_id = source.recipe_id
        source_reasons = source.selection_reasons_json

        source.dish_id = target.dish_id
        source.recipe_id = target.recipe_id
        source.selection_reasons_json = target.selection_reasons_json

        target.dish_id = source_dish_id
        target.recipe_id = source_recipe_id
        target.selection_reasons_json = source_reasons

        plan = self.db.get(MealPlan, source.meal_plan_id)
        if plan is not None:
            clear_undo_snapshot(plan)
        self.db.commit()
        return self.to_item_public(self._load_item(source.id)), self.to_item_public(self._load_item(target.id))

    def assign_meal_slot(
        self,
        *,
        meal_date: date,
        meal_slot: MealSlot,
        dish_id: int,
        recipe_id: int | None = None,
        mode: str = "replace_all",
    ) -> MealPlanItemPublic:
        reference_date = household_local_today(self.db)
        if meal_date < reference_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot assign a dish to a past meal",
            )

        plan = self.get_or_create_plan(meal_date)
        item = next(
            (candidate for candidate in plan.items if candidate.date == meal_date and candidate.meal_slot == meal_slot),
            None,
        )
        if item is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Meal slot not found in the plan week",
            )
        if item.status != MealPlanItemStatus.planned:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only assign dishes to planned meals",
            )
        if item.is_locked:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change dish or recipe on a locked meal",
            )

        clear_undo_snapshot(plan)
        self._apply_assignment(item, dish_id, recipe_id, mode=mode)
        self.db.commit()
        return self.to_item_public(self._load_item(item.id))

    def add_line(self, item_id: int, payload: MealPlanDishLineCreateRequest) -> MealPlanItemPublic:
        item = self._load_item(item_id)
        self._assert_assignment_allowed(item)
        self._assert_slot_mutable(item)
        if item.status != MealPlanItemStatus.planned:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only add dishes to planned meals",
            )
        self._append_manual_line(
            item,
            payload.dish_id,
            payload.recipe_id,
            role=payload.role,
            position=payload.position,
        )
        plan = self.db.get(MealPlan, item.meal_plan_id)
        if plan is not None:
            clear_undo_snapshot(plan)
        self.db.commit()
        return self.to_item_public(self._load_item(item.id))

    def update_line(self, line_id: int, payload: MealPlanDishLineUpdateRequest) -> MealPlanItemPublic:
        line = self._load_line(line_id)
        item = line.meal_plan_item
        self._assert_assignment_allowed(item)
        self._assert_slot_mutable(item)
        updates = payload.model_dump(exclude_unset=True)
        if "dish_id" in updates or "recipe_id" in updates:
            dish_id = updates.get("dish_id", line.dish_id)
            if dish_id is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="dish_id is required")
            if "recipe_id" in updates:
                recipe_id = updates["recipe_id"]
            elif "dish_id" in updates:
                recipe_id = None
            else:
                recipe_id = line.recipe_id
            line.dish_id = dish_id
            line.recipe_id = self._resolve_recipe_for_dish(dish_id, recipe_id)
            dish = self.db.get(Dish, dish_id)
            if dish is not None and "role" not in updates:
                line.role = role_for_dish(dish)
        if "role" in updates and updates["role"] is not None:
            line.role = updates["role"]
        if "position" in updates and updates["position"] is not None:
            line.position = self._resolve_line_position(item, updates["position"], exclude_line_id=line.id)
        sync_legacy_mirror(item)
        self.db.commit()
        return self.to_item_public(self._load_item(item.id))

    def delete_line(self, line_id: int) -> MealPlanItemPublic:
        line = self._load_line(line_id)
        item = line.meal_plan_item
        self._assert_assignment_allowed(item)
        self._assert_slot_mutable(item)
        if item.status != MealPlanItemStatus.planned:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only remove dishes from planned meals",
            )
        item.lines.remove(line)
        self.db.delete(line)
        self.db.flush()
        for index, remaining in enumerate(sorted(item.lines, key=lambda row: row.position)):
            remaining.position = index
        sync_legacy_mirror(item)
        plan = self.db.get(MealPlan, item.meal_plan_id)
        if plan is not None:
            clear_undo_snapshot(plan)
        self.db.commit()
        return self.to_item_public(self._load_item(item.id))

    def mark_do_not_plan(self, item_id: int, payload: MealPlanDoNotPlanRequest) -> MealPlanItemPublic:
        item = self._load_item(item_id)
        self._assert_assignment_allowed(item)
        if item.status != MealPlanItemStatus.planned:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only mark planned meals as do-not-plan",
            )
        item.planning_state = MealPlanningState.do_not_plan
        if payload.remove_existing_lines:
            self._clear_all_lines(item)
        plan = self.db.get(MealPlan, item.meal_plan_id)
        if plan is not None:
            clear_undo_snapshot(plan)
        self.db.commit()
        return self.to_item_public(self._load_item(item.id))

    def reopen_slot(self, item_id: int) -> MealPlanItemPublic:
        item = self._load_item(item_id)
        item.planning_state = MealPlanningState.open
        self.db.commit()
        return self.to_item_public(self._load_item(item.id))

    def _load_line(self, line_id: int) -> MealPlanItemDish:
        line = self.db.scalar(
            select(MealPlanItemDish)
            .where(MealPlanItemDish.id == line_id)
            .options(
                selectinload(MealPlanItemDish.meal_plan_item).options(*self._meal_plan_item_trait_options()),
                selectinload(MealPlanItemDish.dish),
                selectinload(MealPlanItemDish.recipe).options(*RECIPE_TRAIT_INGREDIENT_LOAD),
            )
        )
        if line is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal dish line not found")
        return line
