import re
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from mealroulette.models.catalog import (
    Dish,
    DishSeasonality,
    Ingredient,
    IngredientAlias,
    Recipe,
    RecipeIngredient,
    RecipeStep,
    Tag,
    Unit,
)
from mealroulette.models.enums import SeasonalityMode, SeasonalityStrength
from mealroulette.schemas.catalog import (
    DishCreateRequest,
    DishPublic,
    DishUpdateRequest,
    IngredientAliasCreateRequest,
    IngredientCreateRequest,
    IngredientPublic,
    IngredientResolveResponse,
    IngredientUpdateRequest,
    RecipeCreateRequest,
    RecipeIngredientCreateRequest,
    RecipeIngredientPublic,
    RecipeIngredientUpdateRequest,
    RecipePublic,
    RecipeStepCreateRequest,
    RecipeStepPublic,
    RecipeStepUpdateRequest,
    RecipeUpdateRequest,
    SeasonalityPublic,
    SeasonalityUpsertRequest,
    TagCreateRequest,
    TagPublic,
    TagUpdateRequest,
)


def normalize_name(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


class CatalogService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def to_ingredient_public(ingredient: Ingredient) -> IngredientPublic:
        return IngredientPublic.model_validate(ingredient)

    @staticmethod
    def to_dish_public(dish: Dish) -> DishPublic:
        return DishPublic(
            id=dish.id,
            name=dish.name,
            description=dish.description,
            default_servings=dish.default_servings,
            prep_time_minutes=dish.prep_time_minutes,
            cook_time_minutes=dish.cook_time_minutes,
            difficulty=dish.difficulty,
            active=dish.active,
            notes=dish.notes,
            created_at=dish.created_at,
            updated_at=dish.updated_at,
            tag_ids=[tag.id for tag in dish.tags],
            seasonality=SeasonalityPublic.model_validate(dish.seasonality) if dish.seasonality else None,
        )

    def list_units(self) -> list[Unit]:
        return list(self.db.scalars(select(Unit).order_by(Unit.dimension, Unit.name)))

    def get_unit(self, unit_id: int) -> Unit:
        unit = self.db.get(Unit, unit_id)
        if unit is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")
        return unit

    def list_tags(self, family: str | None = None) -> list[Tag]:
        query = select(Tag).order_by(Tag.family, Tag.name)
        if family:
            query = query.where(Tag.family == family)
        return list(self.db.scalars(query))

    def get_tag(self, tag_id: int) -> Tag:
        tag = self.db.get(Tag, tag_id)
        if tag is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
        return tag

    def create_tag(self, payload: TagCreateRequest) -> Tag:
        if self.db.scalar(select(Tag).where(Tag.family == payload.family, Tag.name == payload.name)):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tag already exists")
        tag = Tag(name=payload.name, family=payload.family, description=payload.description)
        self.db.add(tag)
        self.db.commit()
        self.db.refresh(tag)
        return tag

    def update_tag(self, tag_id: int, payload: TagUpdateRequest) -> Tag:
        tag = self.get_tag(tag_id)
        if payload.name is not None:
            tag.name = payload.name
        if payload.family is not None:
            tag.family = payload.family
        if payload.description is not None:
            tag.description = payload.description
        self.db.commit()
        self.db.refresh(tag)
        return tag

    def delete_tag(self, tag_id: int) -> None:
        tag = self.get_tag(tag_id)
        self.db.delete(tag)
        self.db.commit()

    def list_ingredients(self, search: str | None = None) -> list[Ingredient]:
        query = select(Ingredient).order_by(Ingredient.display_name)
        if search:
            pattern = f"%{search.strip().lower()}%"
            query = query.where(
                or_(
                    func.lower(Ingredient.canonical_name).like(pattern),
                    func.lower(Ingredient.display_name).like(pattern),
                )
            )
        return list(self.db.scalars(query))

    def get_ingredient(self, ingredient_id: int) -> Ingredient:
        ingredient = self.db.get(Ingredient, ingredient_id)
        if ingredient is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingredient not found")
        return ingredient

    def resolve_ingredient(self, proposed_name: str) -> IngredientResolveResponse:
        normalized = normalize_name(proposed_name)
        alias = self.db.scalar(
            select(IngredientAlias)
            .options(selectinload(IngredientAlias.ingredient))
            .where(func.lower(IngredientAlias.alias) == normalized)
        )
        if alias is not None:
            return IngredientResolveResponse(
                status="exact",
                ingredient=self.to_ingredient_public(alias.ingredient),
            )

        exact = self.db.scalar(select(Ingredient).where(func.lower(Ingredient.canonical_name) == normalized))
        if exact is not None:
            return IngredientResolveResponse(status="exact", ingredient=self.to_ingredient_public(exact))

        pattern = f"%{normalized}%"
        suggestions = list(
            self.db.scalars(
                select(Ingredient)
                .where(
                    or_(
                        func.lower(Ingredient.canonical_name).like(pattern),
                        func.lower(Ingredient.display_name).like(pattern),
                    )
                )
                .limit(10)
            )
        )
        if suggestions:
            return IngredientResolveResponse(
                status="suggestions",
                suggestions=[self.to_ingredient_public(item) for item in suggestions],
            )
        return IngredientResolveResponse(status="none")

    def confirm_ingredient(
        self,
        *,
        action: str,
        proposed_name: str,
        ingredient_id: int | None = None,
        display_name: str | None = None,
        category: str | None = None,
        default_unit_id: int | None = None,
        language: str | None = None,
    ) -> Ingredient:
        normalized = normalize_name(proposed_name)
        if action == "create":
            if self.db.scalar(select(Ingredient).where(func.lower(Ingredient.canonical_name) == normalized)):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ingredient already exists")
            ingredient = Ingredient(
                canonical_name=normalized,
                display_name=display_name or proposed_name.strip(),
                category=category,
                default_unit_id=default_unit_id,
            )
            self.db.add(ingredient)
            self.db.flush()
            self.db.add(IngredientAlias(ingredient_id=ingredient.id, alias=normalized, language=language))
            self.db.commit()
            self.db.refresh(ingredient)
            return ingredient

        if action in {"map", "alias"}:
            if ingredient_id is None:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="ingredient_id is required")
            ingredient = self.get_ingredient(ingredient_id)
            if self.db.scalar(select(IngredientAlias).where(func.lower(IngredientAlias.alias) == normalized)):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Alias already exists")
            self.db.add(IngredientAlias(ingredient_id=ingredient.id, alias=normalized, language=language))
            self.db.commit()
            self.db.refresh(ingredient)
            return ingredient

        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid confirm action")

    def create_ingredient(self, payload: IngredientCreateRequest) -> Ingredient:
        canonical = normalize_name(payload.canonical_name)
        if self.db.scalar(select(Ingredient).where(func.lower(Ingredient.canonical_name) == canonical)):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ingredient already exists")
        ingredient = Ingredient(
            canonical_name=canonical,
            display_name=payload.display_name,
            category=payload.category,
            default_unit_id=payload.default_unit_id,
            default_dimension=payload.default_dimension,
            pantry_item=payload.pantry_item,
            season_start_month=payload.season_start_month,
            season_end_month=payload.season_end_month,
            notes=payload.notes,
        )
        self.db.add(ingredient)
        self.db.flush()
        aliases = {canonical, *(normalize_name(alias) for alias in payload.aliases)}
        for alias in aliases:
            self.db.add(IngredientAlias(ingredient_id=ingredient.id, alias=alias))
        self.db.commit()
        self.db.refresh(ingredient)
        return ingredient

    def update_ingredient(self, ingredient_id: int, payload: IngredientUpdateRequest) -> Ingredient:
        ingredient = self.get_ingredient(ingredient_id)
        for field in (
            "display_name",
            "category",
            "default_unit_id",
            "default_dimension",
            "pantry_item",
            "season_start_month",
            "season_end_month",
            "notes",
        ):
            value = getattr(payload, field)
            if value is not None:
                setattr(ingredient, field, value)
        self.db.commit()
        self.db.refresh(ingredient)
        return ingredient

    def delete_ingredient(self, ingredient_id: int) -> None:
        ingredient = self.get_ingredient(ingredient_id)
        self.db.delete(ingredient)
        self.db.commit()

    def list_aliases(self, ingredient_id: int) -> list[IngredientAlias]:
        self.get_ingredient(ingredient_id)
        return list(
            self.db.scalars(
                select(IngredientAlias)
                .where(IngredientAlias.ingredient_id == ingredient_id)
                .order_by(IngredientAlias.alias)
            )
        )

    def create_alias(self, ingredient_id: int, payload: IngredientAliasCreateRequest) -> IngredientAlias:
        ingredient = self.get_ingredient(ingredient_id)
        normalized = normalize_name(payload.alias)
        if self.db.scalar(select(IngredientAlias).where(func.lower(IngredientAlias.alias) == normalized)):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Alias already exists")
        alias = IngredientAlias(ingredient_id=ingredient.id, alias=normalized, language=payload.language)
        self.db.add(alias)
        self.db.commit()
        self.db.refresh(alias)
        return alias

    def delete_alias(self, alias_id: int) -> None:
        alias = self.db.get(IngredientAlias, alias_id)
        if alias is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alias not found")
        self.db.delete(alias)
        self.db.commit()

    def _apply_tags(self, dish: Dish, tag_ids: list[int]) -> None:
        if not tag_ids:
            dish.tags = []
            return
        tags = list(self.db.scalars(select(Tag).where(Tag.id.in_(tag_ids))))
        if len(tags) != len(set(tag_ids)):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or more tags not found")
        dish.tags = tags

    def _apply_seasonality(self, dish: Dish, payload: SeasonalityUpsertRequest | None) -> None:
        if payload is None:
            return
        if dish.seasonality is None:
            dish.seasonality = DishSeasonality(dish_id=dish.id)
        dish.seasonality.seasonality_mode = payload.seasonality_mode
        dish.seasonality.preferred_months = payload.preferred_months
        dish.seasonality.allowed_months = payload.allowed_months
        dish.seasonality.excluded_months = payload.excluded_months
        dish.seasonality.seasonality_strength = payload.seasonality_strength

    def list_dishes(self, active_only: bool = False) -> list[Dish]:
        query = select(Dish).options(selectinload(Dish.tags), selectinload(Dish.seasonality)).order_by(Dish.name)
        if active_only:
            query = query.where(Dish.active.is_(True))
        return list(self.db.scalars(query))

    def get_dish(self, dish_id: int) -> Dish:
        dish = self.db.scalar(
            select(Dish)
            .options(selectinload(Dish.tags), selectinload(Dish.seasonality), selectinload(Dish.recipes))
            .where(Dish.id == dish_id)
        )
        if dish is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dish not found")
        return dish

    def create_dish(self, payload: DishCreateRequest) -> Dish:
        if self.db.scalar(select(Dish).where(Dish.name == payload.name)):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Dish already exists")
        dish = Dish(
            name=payload.name,
            description=payload.description,
            default_servings=payload.default_servings,
            prep_time_minutes=payload.prep_time_minutes,
            cook_time_minutes=payload.cook_time_minutes,
            difficulty=payload.difficulty,
            active=payload.active,
            notes=payload.notes,
        )
        self.db.add(dish)
        self.db.flush()
        self._apply_tags(dish, payload.tag_ids)
        self._apply_seasonality(dish, payload.seasonality)
        self.db.commit()
        self.db.refresh(dish)
        return self.get_dish(dish.id)

    def update_dish(self, dish_id: int, payload: DishUpdateRequest) -> Dish:
        dish = self.get_dish(dish_id)
        if payload.name is not None:
            dish.name = payload.name
        for field in (
            "description",
            "default_servings",
            "prep_time_minutes",
            "cook_time_minutes",
            "difficulty",
            "active",
            "notes",
        ):
            value = getattr(payload, field)
            if value is not None:
                setattr(dish, field, value)
        if payload.tag_ids is not None:
            self._apply_tags(dish, payload.tag_ids)
        if payload.seasonality is not None:
            self._apply_seasonality(dish, payload.seasonality)
        self.db.commit()
        return self.get_dish(dish.id)

    def delete_dish(self, dish_id: int) -> None:
        dish = self.get_dish(dish_id)
        self.db.delete(dish)
        self.db.commit()

    def list_recipes(self, dish_id: int) -> list[Recipe]:
        self.get_dish(dish_id)
        return list(self.db.scalars(select(Recipe).where(Recipe.dish_id == dish_id).order_by(Recipe.variant_name)))

    def get_recipe(self, recipe_id: int) -> Recipe:
        recipe = self.db.get(Recipe, recipe_id)
        if recipe is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
        return recipe

    def create_recipe(self, dish_id: int, payload: RecipeCreateRequest) -> Recipe:
        self.get_dish(dish_id)
        if self.db.scalar(
            select(Recipe).where(Recipe.dish_id == dish_id, Recipe.variant_name == payload.variant_name)
        ):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Recipe variant already exists")
        recipe = Recipe(dish_id=dish_id, **payload.model_dump())
        self.db.add(recipe)
        self.db.commit()
        self.db.refresh(recipe)
        return recipe

    def update_recipe(self, recipe_id: int, payload: RecipeUpdateRequest) -> Recipe:
        recipe = self.get_recipe(recipe_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(recipe, field, value)
        self.db.commit()
        self.db.refresh(recipe)
        return recipe

    def delete_recipe(self, recipe_id: int) -> None:
        recipe = self.get_recipe(recipe_id)
        self.db.delete(recipe)
        self.db.commit()

    def list_steps(self, recipe_id: int) -> list[RecipeStep]:
        self.get_recipe(recipe_id)
        return list(
            self.db.scalars(
                select(RecipeStep).where(RecipeStep.recipe_id == recipe_id).order_by(RecipeStep.step_number)
            )
        )

    def create_step(self, recipe_id: int, payload: RecipeStepCreateRequest) -> RecipeStep:
        self.get_recipe(recipe_id)
        step = RecipeStep(recipe_id=recipe_id, **payload.model_dump())
        self.db.add(step)
        self.db.commit()
        self.db.refresh(step)
        return step

    def update_step(self, step_id: int, payload: RecipeStepUpdateRequest) -> RecipeStep:
        step = self.db.get(RecipeStep, step_id)
        if step is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe step not found")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(step, field, value)
        self.db.commit()
        self.db.refresh(step)
        return step

    def delete_step(self, step_id: int) -> None:
        step = self.db.get(RecipeStep, step_id)
        if step is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe step not found")
        self.db.delete(step)
        self.db.commit()

    def _resolve_ingredient_id(self, ingredient_id: int | None, proposed_name: str | None) -> int:
        if ingredient_id is not None:
            self.get_ingredient(ingredient_id)
            return ingredient_id
        if proposed_name is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="ingredient_id or proposed_name is required",
            )
        resolved = self.resolve_ingredient(proposed_name)
        if resolved.status != "exact" or resolved.ingredient is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ingredient must be resolved before adding to recipe",
            )
        return resolved.ingredient.id

    def list_recipe_ingredients(self, recipe_id: int) -> list[RecipeIngredient]:
        self.get_recipe(recipe_id)
        return list(self.db.scalars(select(RecipeIngredient).where(RecipeIngredient.recipe_id == recipe_id)))

    def add_recipe_ingredient(self, recipe_id: int, payload: RecipeIngredientCreateRequest) -> RecipeIngredient:
        self.get_recipe(recipe_id)
        ingredient_id = self._resolve_ingredient_id(payload.ingredient_id, payload.proposed_name)
        if payload.unit_id is not None:
            self.get_unit(payload.unit_id)
        item = RecipeIngredient(
            recipe_id=recipe_id,
            ingredient_id=ingredient_id,
            quantity=payload.quantity,
            unit_id=payload.unit_id,
            optional=payload.optional,
            notes=payload.notes,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update_recipe_ingredient(self, item_id: int, payload: RecipeIngredientUpdateRequest) -> RecipeIngredient:
        item = self.db.get(RecipeIngredient, item_id)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe ingredient not found")
        if payload.unit_id is not None:
            self.get_unit(payload.unit_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete_recipe_ingredient(self, item_id: int) -> None:
        item = self.db.get(RecipeIngredient, item_id)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe ingredient not found")
        self.db.delete(item)
        self.db.commit()
