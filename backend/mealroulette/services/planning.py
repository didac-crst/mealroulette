from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from mealroulette.models.catalog import Dish, Recipe
from mealroulette.models.enums import MealPlanItemStatus, MealPlanStatus, MealSlot
from mealroulette.models.planning import MealPlan, MealPlanItem, MealRating
from mealroulette.schemas.planning import (
    MealPlanCreateRequest,
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

    @classmethod
    def to_item_public(cls, item: MealPlanItem) -> MealPlanItemPublic:
        prep_time_minutes, cook_time_minutes = cls._meal_times(item)
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
            is_locked=item.is_locked,
            manually_selected=item.manually_selected,
            skip_reason=item.skip_reason,
            skip_comment=item.skip_comment,
            leftover_source_item_id=item.leftover_source_item_id,
            selection_reasons_json=item.selection_reasons_json,
            review_saved_at=item.review_saved_at,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    @classmethod
    def to_plan_public(cls, plan: MealPlan) -> MealPlanPublic:
        items = sorted(plan.items, key=lambda item: (item.date, meal_slot_sort_key(item.meal_slot)))
        return MealPlanPublic(
            id=plan.id,
            week_start_date=plan.week_start_date,
            status=plan.status,
            items=[cls.to_item_public(item) for item in items],
            created_at=plan.created_at,
            updated_at=plan.updated_at,
        )

    def _load_plan(self, plan_id: int) -> MealPlan:
        plan = self.db.scalar(
            select(MealPlan)
            .where(MealPlan.id == plan_id)
            .options(
                selectinload(MealPlan.items).selectinload(MealPlanItem.dish),
                selectinload(MealPlan.items).selectinload(MealPlanItem.recipe),
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
                selectinload(MealPlanItem.dish),
                selectinload(MealPlanItem.recipe),
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
                selectinload(MealPlan.items).selectinload(MealPlanItem.dish),
                selectinload(MealPlan.items).selectinload(MealPlanItem.recipe),
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
        plan = self.get_or_create_plan(date.today())
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

    def _apply_assignment(self, item: MealPlanItem, dish_id: int | None, recipe_id: int | None) -> None:
        if dish_id is None:
            if item.status != MealPlanItemStatus.planned:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot clear dish on a meal that has already been reviewed",
                )
            item.dish_id = None
            item.recipe_id = None
            item.manually_selected = False
            return
        dish = self.db.get(Dish, dish_id)
        if dish is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dish not found")
        item.dish_id = dish_id
        item.recipe_id = self._resolve_recipe_for_dish(dish_id, recipe_id)
        item.manually_selected = True
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
        if item.dish_id is None:
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
        if item.dish_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assign a dish before locking the meal",
            )
        item.is_locked = True
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
            .options(selectinload(MealPlanItem.dish), selectinload(MealPlanItem.recipe))
            .order_by(MealPlanItem.date.desc(), MealPlanItem.meal_slot.desc())
            .limit(limit)
        )
        return [self.to_item_public(item) for item in items]
