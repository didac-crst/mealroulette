from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from mealroulette.models.catalog import Dish, Ingredient, Recipe, RecipeIngredient, RecipeStep, Tag, Unit
from mealroulette.models.enums import DishStatus, MealComposition, RecipeType
from mealroulette.models.public_catalog import PublicRecipe, PublicRecipeStatus, PublicRecipeVersion
from mealroulette.models.user import User
from mealroulette.schemas.catalog import (
    DishCreateRequest,
    RecipeCreateRequest,
    RecipeIngredientCreateRequest,
    RecipeStepCreateRequest,
)
from mealroulette.schemas.public_catalog import (
    PublicRecipeAdoptResponse,
    PublicRecipeApproveRequest,
    PublicRecipeHouseholdPublic,
    PublicRecipeMemberPublic,
    PublicRecipePlatformPublic,
    PublicRecipeReviewNoteRequest,
    PublicRecipeStatusValue,
    PublicRecipeVersionPublic,
)
from mealroulette.services.catalog import CatalogService

_BLOCKING_SUBMIT_STATUSES = frozenset(
    {
        PublicRecipeStatus.submitted.value,
        PublicRecipeStatus.public.value,
        PublicRecipeStatus.delisted.value,
    }
)
_RESUBMIT_STATUSES = frozenset(
    {
        PublicRecipeStatus.rejected.value,
        PublicRecipeStatus.withdrawn.value,
    }
)


def _enum_value(value: Any) -> Any:
    if value is None:
        return None
    return value.value if hasattr(value, "value") else value


def _decimal_or_none(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return format(value, "f")


class PublicCatalogService:
    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def _title_from_snapshot(snapshot: dict[str, Any]) -> str:
        dish = snapshot.get("dish") or {}
        recipe = snapshot.get("recipe") or {}
        dish_name = str(dish.get("name") or "Untitled dish")
        variant = recipe.get("variant_name")
        if variant and variant != "Main":
            return f"{dish_name} — {variant}"
        return dish_name

    @staticmethod
    def _description_from_snapshot(snapshot: dict[str, Any]) -> str | None:
        recipe = snapshot.get("recipe") or {}
        dish = snapshot.get("dish") or {}
        return recipe.get("description") or dish.get("description")

    def _latest_version(self, public_recipe: PublicRecipe) -> PublicRecipeVersion | None:
        if not public_recipe.versions:
            return None
        return max(public_recipe.versions, key=lambda item: item.version_number)

    def _current_version(self, public_recipe: PublicRecipe) -> PublicRecipeVersion | None:
        if public_recipe.current_version_id is None:
            return None
        for version in public_recipe.versions:
            if version.id == public_recipe.current_version_id:
                return version
        return self.db.get(PublicRecipeVersion, public_recipe.current_version_id)

    def to_version_public(self, version: PublicRecipeVersion) -> PublicRecipeVersionPublic:
        return PublicRecipeVersionPublic.model_validate(version)

    def to_member_public(self, public_recipe: PublicRecipe) -> PublicRecipeMemberPublic:
        version = self._current_version(public_recipe)
        if version is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Public recipe not found",
            )
        snapshot = version.snapshot_json
        return PublicRecipeMemberPublic(
            id=public_recipe.id,
            status=PublicRecipeStatusValue(public_recipe.status),
            title=self._title_from_snapshot(snapshot),
            description=self._description_from_snapshot(snapshot),
            current_version=self.to_version_public(version),
            snapshot=snapshot,
            created_at=public_recipe.created_at,
            updated_at=public_recipe.updated_at,
        )

    def to_household_public(self, public_recipe: PublicRecipe) -> PublicRecipeHouseholdPublic:
        latest = self._latest_version(public_recipe)
        snapshot = latest.snapshot_json if latest else {}
        return PublicRecipeHouseholdPublic(
            id=public_recipe.id,
            status=PublicRecipeStatusValue(public_recipe.status),
            originating_dish_id=public_recipe.originating_dish_id,
            originating_recipe_id=public_recipe.originating_recipe_id,
            current_version_id=public_recipe.current_version_id,
            title=self._title_from_snapshot(snapshot),
            description=self._description_from_snapshot(snapshot),
            review_note=public_recipe.review_note,
            reviewed_at=public_recipe.reviewed_at,
            latest_version=self.to_version_public(latest) if latest else None,
            created_at=public_recipe.created_at,
            updated_at=public_recipe.updated_at,
        )

    def to_platform_public(self, public_recipe: PublicRecipe) -> PublicRecipePlatformPublic:
        latest = self._latest_version(public_recipe)
        current = self._current_version(public_recipe)
        snapshot_source = current or latest
        snapshot = snapshot_source.snapshot_json if snapshot_source else None
        return PublicRecipePlatformPublic(
            id=public_recipe.id,
            status=PublicRecipeStatusValue(public_recipe.status),
            originating_household_id=public_recipe.originating_household_id,
            originating_dish_id=public_recipe.originating_dish_id,
            originating_recipe_id=public_recipe.originating_recipe_id,
            current_version_id=public_recipe.current_version_id,
            submitted_by_user_id=public_recipe.submitted_by_user_id,
            reviewed_by_user_id=public_recipe.reviewed_by_user_id,
            reviewed_at=public_recipe.reviewed_at,
            review_note=public_recipe.review_note,
            title=self._title_from_snapshot(snapshot or {}),
            description=self._description_from_snapshot(snapshot or {}),
            latest_version=self.to_version_public(latest) if latest else None,
            current_version=self.to_version_public(current) if current else None,
            snapshot=snapshot,
            created_at=public_recipe.created_at,
            updated_at=public_recipe.updated_at,
        )

    def _load_source_recipe(self, recipe_id: int, *, household_id: UUID) -> Recipe:
        recipe = self.db.scalar(
            select(Recipe)
            .join(Dish, Recipe.dish_id == Dish.id)
            .where(Recipe.id == recipe_id, Dish.household_id == household_id)
            .options(
                selectinload(Recipe.dish).selectinload(Dish.tags),
                selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient),
                selectinload(Recipe.ingredients).selectinload(RecipeIngredient.unit),
                selectinload(Recipe.steps),
            )
        )
        if recipe is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
        return recipe

    def build_snapshot(self, recipe: Recipe) -> dict[str, Any]:
        dish = recipe.dish
        ingredients: list[dict[str, Any]] = []
        for item in sorted(recipe.ingredients, key=lambda row: row.id):
            unit: Unit | None = item.unit
            ingredient: Ingredient = item.ingredient
            ingredients.append(
                {
                    "ingredient_id": ingredient.id,
                    "ingredient_canonical_name": ingredient.canonical_name,
                    "ingredient_display_name": ingredient.display_name,
                    "quantity": _decimal_or_none(item.quantity),
                    "unit_id": item.unit_id,
                    "unit_symbol": unit.symbol if unit else None,
                    "unit_name": unit.name if unit else None,
                    "optional": item.optional,
                    "notes": item.notes,
                }
            )
        steps = [
            {
                "step_number": step.step_number,
                "instruction": step.instruction,
                "duration_seconds": step.duration_seconds,
                "temperature": step.temperature,
                "timer_seconds": step.timer_seconds,
                "is_thermomix_step": step.is_thermomix_step,
                "metadata_json": step.metadata_json,
            }
            for step in sorted(recipe.steps, key=lambda row: row.step_number)
        ]
        return {
            "schema_version": 1,
            "dish": {
                "name": dish.name,
                "description": dish.description,
                "default_servings": dish.default_servings,
                "default_prep_time_minutes": dish.default_prep_time_minutes,
                "default_cook_time_minutes": dish.default_cook_time_minutes,
                "default_difficulty": dish.default_difficulty,
                "course": _enum_value(dish.course),
                "meal_composition": _enum_value(dish.meal_composition),
                "simple_dish_part": _enum_value(dish.simple_dish_part),
                "status": _enum_value(dish.status) or DishStatus.active.value,
                "image_url": dish.image_url,
                "suitable_for_lunch": dish.suitable_for_lunch,
                "suitable_for_dinner": dish.suitable_for_dinner,
                "weekday_friendly": dish.weekday_friendly,
                "leftovers_possible": dish.leftovers_possible,
                "freezer_friendly": dish.freezer_friendly,
                "kids_friendly": dish.kids_friendly,
                "notes": dish.notes,
                "tag_ids": [tag.id for tag in dish.tags],
            },
            "recipe": {
                "variant_name": recipe.variant_name,
                "description": recipe.description,
                "recipe_type": _enum_value(recipe.recipe_type) or RecipeType.standard.value,
                "is_main": recipe.is_main,
                "is_thermomix": recipe.is_thermomix,
                "thermomix_model": recipe.thermomix_model,
                "source_url": recipe.source_url,
                "servings": recipe.servings,
                "prep_time_minutes": recipe.prep_time_minutes,
                "cook_time_minutes": recipe.cook_time_minutes,
                "difficulty": recipe.difficulty,
                "notes": recipe.notes,
            },
            "ingredients": ingredients,
            "steps": steps,
        }

    def get_public_recipe(self, public_recipe_id: UUID, *, for_update: bool = False) -> PublicRecipe:
        query = (
            select(PublicRecipe)
            .where(PublicRecipe.id == public_recipe_id)
            .options(selectinload(PublicRecipe.versions))
        )
        if for_update:
            query = query.with_for_update()
        public_recipe = self.db.scalar(query)
        if public_recipe is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Public recipe not found")
        return public_recipe

    def _get_lineage_for_recipe(
        self, originating_recipe_id: int, *, for_update: bool = False
    ) -> PublicRecipe | None:
        query = (
            select(PublicRecipe)
            .where(PublicRecipe.originating_recipe_id == originating_recipe_id)
            .options(selectinload(PublicRecipe.versions))
        )
        if for_update:
            query = query.with_for_update()
        return self.db.scalar(query)

    def submit_publish_request(
        self,
        *,
        user: User,
        household_id: UUID,
        recipe_id: int,
    ) -> PublicRecipe:
        recipe = self._load_source_recipe(recipe_id, household_id=household_id)
        if not recipe.ingredients:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Recipe must have at least one ingredient before publication",
            )
        if not recipe.steps:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Recipe must have at least one step before publication",
            )
        snapshot = self.build_snapshot(recipe)
        existing = self._get_lineage_for_recipe(recipe_id, for_update=True)
        if existing is None:
            public_recipe = PublicRecipe(
                originating_household_id=household_id,
                originating_dish_id=recipe.dish_id,
                originating_recipe_id=recipe.id,
                current_version_id=None,
                status=PublicRecipeStatus.submitted.value,
                submitted_by_user_id=user.id,
                reviewed_by_user_id=None,
                reviewed_at=None,
                review_note=None,
            )
            self.db.add(public_recipe)
            self.db.flush()
            version = PublicRecipeVersion(
                public_recipe_id=public_recipe.id,
                version_number=1,
                snapshot_json=snapshot,
                published_at=None,
                superseded_at=None,
                created_by_user_id=user.id,
            )
            self.db.add(version)
            self.db.commit()
            return self.get_public_recipe(public_recipe.id)

        if existing.status in _BLOCKING_SUBMIT_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot submit publication request in status {existing.status}",
            )
        if existing.status not in _RESUBMIT_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot submit publication request in status {existing.status}",
            )

        latest = self._latest_version(existing)
        next_number = (latest.version_number if latest else 0) + 1
        version = PublicRecipeVersion(
            public_recipe_id=existing.id,
            version_number=next_number,
            snapshot_json=snapshot,
            published_at=None,
            superseded_at=None,
            created_by_user_id=user.id,
        )
        self.db.add(version)
        existing.status = PublicRecipeStatus.submitted.value
        existing.submitted_by_user_id = user.id
        existing.reviewed_by_user_id = None
        existing.reviewed_at = None
        existing.review_note = None
        existing.current_version_id = None
        self.db.commit()
        return self.get_public_recipe(existing.id)

    def list_household_requests(self, *, household_id: UUID) -> list[PublicRecipe]:
        return list(
            self.db.scalars(
                select(PublicRecipe)
                .where(PublicRecipe.originating_household_id == household_id)
                .options(selectinload(PublicRecipe.versions))
                .order_by(PublicRecipe.updated_at.desc())
            )
        )

    def withdraw(
        self,
        *,
        public_recipe_id: UUID,
        household_id: UUID,
    ) -> PublicRecipe:
        public_recipe = self.get_public_recipe(public_recipe_id, for_update=True)
        if public_recipe.originating_household_id != household_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Public recipe not found")
        if public_recipe.status != PublicRecipeStatus.submitted.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot withdraw publication request in status {public_recipe.status}",
            )
        public_recipe.status = PublicRecipeStatus.withdrawn.value
        self.db.commit()
        return self.get_public_recipe(public_recipe.id)

    def list_public(self) -> list[PublicRecipe]:
        return list(
            self.db.scalars(
                select(PublicRecipe)
                .where(
                    PublicRecipe.status == PublicRecipeStatus.public.value,
                    PublicRecipe.current_version_id.is_not(None),
                )
                .options(selectinload(PublicRecipe.versions))
                .order_by(PublicRecipe.updated_at.desc())
            )
        )

    def get_public_for_members(self, public_recipe_id: UUID) -> PublicRecipe:
        public_recipe = self.get_public_recipe(public_recipe_id)
        if (
            public_recipe.status != PublicRecipeStatus.public.value
            or public_recipe.current_version_id is None
        ):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Public recipe not found")
        return public_recipe

    def list_for_platform(self, *, status_filter: str | None = None) -> list[PublicRecipe]:
        query = select(PublicRecipe).options(selectinload(PublicRecipe.versions))
        if status_filter is not None:
            try:
                PublicRecipeStatus(status_filter)
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unknown status filter: {status_filter}",
                ) from exc
            query = query.where(PublicRecipe.status == status_filter)
        return list(self.db.scalars(query.order_by(PublicRecipe.updated_at.desc())))

    def _require_submitted(self, public_recipe_id: UUID) -> PublicRecipe:
        public_recipe = self.get_public_recipe(public_recipe_id, for_update=True)
        if public_recipe.status != PublicRecipeStatus.submitted.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot review publication request in status {public_recipe.status}",
            )
        return public_recipe

    def approve(
        self,
        *,
        public_recipe_id: UUID,
        reviewer: User,
        payload: PublicRecipeApproveRequest,
    ) -> PublicRecipe:
        public_recipe = self._require_submitted(public_recipe_id)
        latest = self._latest_version(public_recipe)
        if latest is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Publication request has no version to approve",
            )
        now = datetime.now(timezone.utc)
        previous = self._current_version(public_recipe)
        if previous is not None and previous.id != latest.id:
            previous.superseded_at = now
        latest.published_at = now
        public_recipe.current_version_id = latest.id
        public_recipe.status = PublicRecipeStatus.public.value
        public_recipe.reviewed_by_user_id = reviewer.id
        public_recipe.reviewed_at = now
        public_recipe.review_note = payload.review_note
        self.db.commit()
        return self.get_public_recipe(public_recipe.id)

    def reject(
        self,
        *,
        public_recipe_id: UUID,
        reviewer: User,
        payload: PublicRecipeReviewNoteRequest,
    ) -> PublicRecipe:
        public_recipe = self._require_submitted(public_recipe_id)
        now = datetime.now(timezone.utc)
        public_recipe.status = PublicRecipeStatus.rejected.value
        public_recipe.reviewed_by_user_id = reviewer.id
        public_recipe.reviewed_at = now
        public_recipe.review_note = payload.review_note
        self.db.commit()
        return self.get_public_recipe(public_recipe.id)

    def delist(
        self,
        *,
        public_recipe_id: UUID,
        reviewer: User,
        payload: PublicRecipeReviewNoteRequest,
    ) -> PublicRecipe:
        public_recipe = self.get_public_recipe(public_recipe_id, for_update=True)
        if public_recipe.status != PublicRecipeStatus.public.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot delist publication in status {public_recipe.status}",
            )
        now = datetime.now(timezone.utc)
        public_recipe.status = PublicRecipeStatus.delisted.value
        public_recipe.reviewed_by_user_id = reviewer.id
        public_recipe.reviewed_at = now
        public_recipe.review_note = payload.review_note
        self.db.commit()
        return self.get_public_recipe(public_recipe.id)

    def _unique_adopt_dish_name(self, catalog: CatalogService, base_name: str) -> str:
        candidates = [base_name, f"{base_name} (adopted)"]
        short = base_name[:200]
        for suffix in range(2, 20):
            candidates.append(f"{short} (adopted {suffix})")
        for name in candidates:
            exists = self.db.scalar(
                select(Dish.id).where(Dish.name == name, Dish.household_id == catalog.household_id)
            )
            if exists is None:
                return name
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Could not allocate a unique dish name for adoption",
        )

    def adopt(
        self,
        *,
        public_recipe_id: UUID,
        household_id: UUID,
    ) -> PublicRecipeAdoptResponse:
        public_recipe = self.get_public_for_members(public_recipe_id)
        version = self._current_version(public_recipe)
        if version is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Public recipe not found")
        snapshot = version.snapshot_json
        dish_data = snapshot.get("dish") or {}
        recipe_data = snapshot.get("recipe") or {}
        catalog = CatalogService(self.db, household_id=household_id)
        dish_name = self._unique_adopt_dish_name(catalog, str(dish_data.get("name") or "Adopted dish"))
        meal_composition = dish_data.get("meal_composition") or MealComposition.main_dish.value
        requested_tag_ids = [int(tag_id) for tag_id in (dish_data.get("tag_ids") or [])]
        existing_tag_ids: list[int] = []
        if requested_tag_ids:
            existing_tag_ids = list(
                self.db.scalars(select(Tag.id).where(Tag.id.in_(requested_tag_ids)))
            )
        try:
            dish = catalog.create_dish(
                DishCreateRequest(
                    name=dish_name,
                    description=dish_data.get("description"),
                    default_servings=dish_data.get("default_servings"),
                    default_prep_time_minutes=dish_data.get("default_prep_time_minutes"),
                    default_cook_time_minutes=dish_data.get("default_cook_time_minutes"),
                    default_difficulty=dish_data.get("default_difficulty"),
                    course=dish_data.get("course"),
                    meal_composition=meal_composition,
                    simple_dish_part=dish_data.get("simple_dish_part"),
                    status=DishStatus.active,
                    image_url=dish_data.get("image_url"),
                    suitable_for_lunch=dish_data.get("suitable_for_lunch"),
                    suitable_for_dinner=dish_data.get("suitable_for_dinner"),
                    weekday_friendly=dish_data.get("weekday_friendly"),
                    leftovers_possible=dish_data.get("leftovers_possible"),
                    freezer_friendly=dish_data.get("freezer_friendly"),
                    kids_friendly=dish_data.get("kids_friendly"),
                    notes=dish_data.get("notes"),
                    tag_ids=existing_tag_ids,
                ),
                commit=False,
            )
            recipe = catalog.create_recipe(
                dish.id,
                RecipeCreateRequest(
                    variant_name=str(recipe_data.get("variant_name") or "Main"),
                    description=recipe_data.get("description"),
                    recipe_type=recipe_data.get("recipe_type"),
                    is_main=bool(recipe_data.get("is_main", True)),
                    is_thermomix=recipe_data.get("is_thermomix"),
                    thermomix_model=recipe_data.get("thermomix_model"),
                    source_url=recipe_data.get("source_url"),
                    servings=recipe_data.get("servings"),
                    prep_time_minutes=recipe_data.get("prep_time_minutes"),
                    cook_time_minutes=recipe_data.get("cook_time_minutes"),
                    difficulty=recipe_data.get("difficulty"),
                    notes=recipe_data.get("notes"),
                ),
                commit=False,
            )
            for item in snapshot.get("ingredients") or []:
                quantity = item.get("quantity")
                catalog.add_recipe_ingredient(
                    recipe.id,
                    RecipeIngredientCreateRequest(
                        ingredient_id=item["ingredient_id"],
                        quantity=Decimal(quantity) if quantity is not None else None,
                        unit_id=item.get("unit_id"),
                        optional=bool(item.get("optional", False)),
                        notes=item.get("notes"),
                    ),
                    commit=False,
                )
            for step in snapshot.get("steps") or []:
                catalog.create_step(
                    recipe.id,
                    RecipeStepCreateRequest(
                        step_number=int(step["step_number"]),
                        instruction=str(step["instruction"]),
                        duration_seconds=step.get("duration_seconds"),
                        temperature=step.get("temperature"),
                        timer_seconds=step.get("timer_seconds"),
                        is_thermomix_step=bool(step.get("is_thermomix_step", False)),
                        metadata_json=step.get("metadata_json"),
                    ),
                    commit=False,
                )
            owned = catalog.get_recipe(recipe.id)
            owned.derived_from_public_recipe_id = public_recipe.id
            owned.derived_from_public_version_id = version.id
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(owned)
        self.db.refresh(dish)
        return PublicRecipeAdoptResponse(
            dish_id=dish.id,
            recipe_id=owned.id,
            dish_public_key=dish.public_key,
            recipe_public_key=owned.public_key,
            derived_from_public_recipe_id=public_recipe.id,
            derived_from_public_version_id=version.id,
        )
