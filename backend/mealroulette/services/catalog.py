from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from mealroulette.models.catalog import (
    Dish,
    DishSeasonality,
    Ingredient,
    IngredientAlias,
    IngredientUnitConversion,
    Recipe,
    RecipeIngredient,
    RecipeStep,
    Tag,
    Unit,
)
from mealroulette.models.household import DEFAULT_HOUSEHOLD_ID
from mealroulette.data.seed_taxonomy import resolve_family_fields
from mealroulette.models.enums import (
    AggregationStrategy,
    ConversionSource,
    DishStatus,
    MealComposition,
    RecipeType,
    SeasonalityMode,
    SeasonalityStrength,
)
from mealroulette.schemas.catalog import validate_meal_composition_fields
from mealroulette.services.food_groups import food_group_for_ingredient
from mealroulette.services.ingredient_resolver import IngredientResolverService
from mealroulette.services.names import normalize_name
from mealroulette.services.public_keys import generate_dish_public_key, generate_recipe_public_key
from mealroulette.services.recipe_traits import compute_recipe_traits_now, refresh_recipe_traits, refresh_recipes_for_ingredient
from mealroulette.services.quantities import UnitInfo
from mealroulette.services.scheduler.catalog import load_reference_units
from mealroulette.schemas.catalog import (
    DishCreateRequest,
    DishPublic,
    DishUpdateRequest,
    IngredientAliasCreateRequest,
    IngredientAliasPublic,
    IngredientConfirmAction,
    IngredientCreateRequest,
    IngredientDetailPublic,
    IngredientPublic,
    IngredientResolveResponse,
    IngredientUnitConversionCreateRequest,
    IngredientUnitConversionPublic,
    IngredientUnitConversionUpdateRequest,
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


class CatalogService:
    _INHERITED_DISH_FIELDS = frozenset(
        {
            "default_prep_time_minutes",
            "default_cook_time_minutes",
            "default_difficulty",
            "serving_temperature",
            "thermomix_possible",
            "vegetable_level",
            "dominant_protein",
            "dominant_carb",
        }
    )

    def __init__(self, db: Session, household_id: UUID = DEFAULT_HOUSEHOLD_ID):
        self.db = db
        self.household_id = household_id

    def _assert_dish_in_household(self, dish: Dish) -> None:
        if dish.household_id != self.household_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dish not found")

    @staticmethod
    def _validate_dish_meal_composition(dish: Dish) -> None:
        try:
            validate_meal_composition_fields(dish.meal_composition, dish.simple_dish_part)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc

    @staticmethod
    def _main_recipe(dish: Dish) -> Recipe | None:
        if not dish.recipes:
            return None
        mains = [recipe for recipe in dish.recipes if recipe.is_main]
        if len(mains) == 1:
            return mains[0]
        if len(mains) > 1:
            return min(mains, key=lambda recipe: recipe.id)
        return min(dish.recipes, key=lambda recipe: recipe.id)

    @staticmethod
    def _thermomix_possible_from_recipes(recipes: list[Recipe]) -> bool | None:
        if not recipes:
            return None
        return any(recipe.recipe_type == RecipeType.thermomix or recipe.is_thermomix for recipe in recipes)

    def _generate_unique_dish_public_key(self, name: str) -> str:
        for _ in range(20):
            public_key = generate_dish_public_key(name)
            # Dish public keys remain globally unique: recipe keys are derived from them
            # and recipes keep a global unique index.
            if self.db.scalar(select(Dish.id).where(Dish.public_key == public_key)) is None:
                return public_key
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not generate unique dish public key",
        )

    def _next_recipe_sequence_number(self, dish_id: int) -> int:
        current = self.db.scalar(select(func.max(Recipe.sequence_number)).where(Recipe.dish_id == dish_id))
        return int(current or 0) + 1

    @staticmethod
    def _recipe_public_key(dish: Dish, sequence_number: int) -> str:
        return generate_recipe_public_key(dish.public_key, sequence_number)

    def _reference_units(self):
        return load_reference_units(self.db)

    def _refresh_recipe_traits(self, recipe: Recipe) -> None:
        gram_unit, ml_unit = self._reference_units()
        refresh_recipe_traits(self.db, recipe, gram_unit=gram_unit, ml_unit=ml_unit)

    def _refresh_recipes_for_ingredient(self, ingredient_id: int) -> None:
        gram_unit, ml_unit = self._reference_units()
        refresh_recipes_for_ingredient(
            self.db,
            ingredient_id,
            gram_unit=gram_unit,
            ml_unit=ml_unit,
        )

    def to_recipe_public(
        self,
        recipe: Recipe,
        *,
        computed_traits: dict | None = None,
        gram_unit: UnitInfo | None = None,
        ml_unit: UnitInfo | None = None,
    ) -> RecipePublic:
        if computed_traits is None:
            if gram_unit is None or ml_unit is None:
                gram_unit, ml_unit = self._reference_units()
            traits = compute_recipe_traits_now(self.db, recipe, gram_unit=gram_unit, ml_unit=ml_unit)
        else:
            traits = computed_traits
        return RecipePublic.model_validate(recipe).model_copy(update={"computed_traits_json": traits})

    def to_dish_public(
        self,
        dish: Dish,
        *,
        gram_unit: UnitInfo | None = None,
        ml_unit: UnitInfo | None = None,
    ) -> DishPublic:
        main_recipe = self._main_recipe(dish)
        traits = None
        if main_recipe is not None:
            if gram_unit is None or ml_unit is None:
                gram_unit, ml_unit = self._reference_units()
            traits = compute_recipe_traits_now(self.db, main_recipe, gram_unit=gram_unit, ml_unit=ml_unit)
        return DishPublic(
            id=dish.id,
            public_key=dish.public_key,
            name=dish.name,
            description=dish.description,
            default_servings=dish.default_servings,
            default_prep_time_minutes=main_recipe.prep_time_minutes if main_recipe else None,
            default_cook_time_minutes=main_recipe.cook_time_minutes if main_recipe else None,
            default_difficulty=main_recipe.difficulty if main_recipe else None,
            course=dish.course,
            meal_composition=dish.meal_composition,
            simple_dish_part=dish.simple_dish_part,
            status=dish.status,
            image_url=dish.image_url,
            suitable_for_lunch=dish.suitable_for_lunch,
            suitable_for_dinner=dish.suitable_for_dinner,
            weekday_friendly=dish.weekday_friendly,
            leftovers_possible=dish.leftovers_possible,
            freezer_friendly=dish.freezer_friendly,
            kids_friendly=dish.kids_friendly,
            thermomix_possible=self._thermomix_possible_from_recipes(dish.recipes),
            active=dish.status == DishStatus.active,
            notes=dish.notes,
            created_at=dish.created_at,
            updated_at=dish.updated_at,
            tag_ids=[tag.id for tag in dish.tags],
            computed_traits_json=traits,
            seasonality=SeasonalityPublic.model_validate(dish.seasonality) if dish.seasonality else None,
        )

    def list_dishes_public(self, active_only: bool = False) -> list[DishPublic]:
        gram_unit, ml_unit = self._reference_units()
        return [
            self.to_dish_public(dish, gram_unit=gram_unit, ml_unit=ml_unit)
            for dish in self.list_dishes(active_only)
        ]

    def list_recipes_public(self, dish_id: int) -> list[RecipePublic]:
        gram_unit, ml_unit = self._reference_units()
        return [
            self.to_recipe_public(recipe, gram_unit=gram_unit, ml_unit=ml_unit)
            for recipe in self.list_recipes(dish_id)
        ]

    @staticmethod
    def to_ingredient_public(ingredient: Ingredient) -> IngredientPublic:
        return IngredientPublic.model_validate(ingredient)

    @staticmethod
    def to_conversion_public(conversion: IngredientUnitConversion) -> IngredientUnitConversionPublic:
        return IngredientUnitConversionPublic(
            id=conversion.id,
            ingredient_id=conversion.ingredient_id,
            from_unit_id=conversion.from_unit_id,
            to_unit_id=conversion.to_unit_id,
            from_unit_symbol=conversion.from_unit.symbol,
            to_unit_symbol=conversion.to_unit.symbol,
            factor=conversion.factor,
            confidence=conversion.confidence,
            notes=conversion.notes,
            approved=conversion.approved,
            source=conversion.source,
            created_at=conversion.created_at,
            updated_at=conversion.updated_at,
        )

    def to_ingredient_detail(self, ingredient: Ingredient) -> IngredientDetailPublic:
        return IngredientDetailPublic(
            **self.to_ingredient_public(ingredient).model_dump(),
            aliases=[IngredientAliasPublic.model_validate(alias) for alias in ingredient.aliases],
            unit_conversions=[self.to_conversion_public(conversion) for conversion in ingredient.unit_conversions],
        )

    def _set_main_recipe(self, dish_id: int, recipe_id: int) -> None:
        recipes = list(self.db.scalars(select(Recipe).where(Recipe.dish_id == dish_id)))
        for recipe in recipes:
            recipe.is_main = recipe.id == recipe_id

    @staticmethod
    def _resolve_recipe_type(
        recipe_type: RecipeType | None,
        is_thermomix: bool | None,
        current: RecipeType = RecipeType.standard,
    ) -> RecipeType:
        if recipe_type is not None:
            return recipe_type
        if is_thermomix is True:
            return RecipeType.thermomix
        if is_thermomix is False and current == RecipeType.thermomix:
            return RecipeType.standard
        return current

    @staticmethod
    def _apply_recipe_type(recipe: Recipe, recipe_type: RecipeType) -> None:
        recipe.recipe_type = recipe_type
        recipe.is_thermomix = recipe_type == RecipeType.thermomix

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
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(tag, field, value)
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
            alias_match = (
                select(IngredientAlias.ingredient_id)
                .where(func.lower(IngredientAlias.alias).like(pattern))
                .scalar_subquery()
            )
            query = query.where(
                or_(
                    func.lower(Ingredient.canonical_name).like(pattern),
                    func.lower(Ingredient.display_name).like(pattern),
                    func.lower(Ingredient.category).like(pattern),
                    Ingredient.id.in_(alias_match),
                )
            )
        return list(self.db.scalars(query))

    def get_ingredient(self, ingredient_id: int) -> Ingredient:
        ingredient = self.db.scalar(
            select(Ingredient)
            .options(
                selectinload(Ingredient.aliases),
                selectinload(Ingredient.unit_conversions).selectinload(IngredientUnitConversion.from_unit),
                selectinload(Ingredient.unit_conversions).selectinload(IngredientUnitConversion.to_unit),
            )
            .where(Ingredient.id == ingredient_id)
        )
        if ingredient is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingredient not found")
        return ingredient

    def resolve_ingredient(self, proposed_name: str) -> IngredientResolveResponse:
        raw = IngredientResolverService(self.db).resolve(proposed_name)
        ingredient_ids: list[int] = []
        if raw.get("ingredient") and raw["ingredient"].get("id") is not None:
            ingredient_ids.append(int(raw["ingredient"]["id"]))
        for item in raw.get("suggestions") or []:
            if item.get("id") is not None:
                ingredient_ids.append(int(item["id"]))

        by_id: dict[int, Ingredient] = {}
        if ingredient_ids:
            for loaded in self.db.scalars(select(Ingredient).where(Ingredient.id.in_(ingredient_ids))):
                by_id[loaded.id] = loaded

        ingredient = None
        if raw.get("ingredient"):
            match_id = raw["ingredient"].get("id")
            if match_id is not None and int(match_id) in by_id:
                ingredient = self.to_ingredient_public(by_id[int(match_id)])

        suggestions = [
            self.to_ingredient_public(by_id[int(item["id"])])
            for item in (raw.get("suggestions") or [])
            if item.get("id") is not None and int(item["id"]) in by_id
        ]

        return IngredientResolveResponse(
            status=raw["status"],
            query=raw.get("query"),
            matched_on=raw.get("matched_on"),
            matched_value=raw.get("matched_value"),
            ingredient=ingredient,
            suggestions=suggestions,
        )

    def confirm_ingredient(
        self,
        *,
        action: IngredientConfirmAction,
        proposed_name: str,
        ingredient_id: int | None = None,
        display_name: str | None = None,
        category: str | None = None,
        default_unit_id: int | None = None,
        language: str | None = None,
    ) -> Ingredient:
        normalized = normalize_name(proposed_name)
        if action == IngredientConfirmAction.create:
            if self.db.scalar(select(Ingredient).where(func.lower(Ingredient.canonical_name) == normalized)):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ingredient already exists")
            ingredient = Ingredient(
                canonical_name=normalized,
                display_name=display_name or proposed_name.strip(),
                category=category,
                food_group=food_group_for_ingredient(food_group=None, category=category, family=None),
                default_unit_id=default_unit_id,
            )
            self.db.add(ingredient)
            self.db.flush()
            self.db.add(IngredientAlias(ingredient_id=ingredient.id, alias=normalized, language=language))
            self.db.commit()
            self.db.refresh(ingredient)
            return ingredient

        if action in {IngredientConfirmAction.map, IngredientConfirmAction.alias}:
            if ingredient_id is None:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="ingredient_id is required")
            ingredient = self.get_ingredient(ingredient_id)
            if self.db.scalar(select(IngredientAlias).where(func.lower(IngredientAlias.alias) == normalized)):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Alias already exists")
            self.db.add(IngredientAlias(ingredient_id=ingredient.id, alias=normalized, language=language))
            self.db.commit()
            self.db.refresh(ingredient)
            return ingredient

        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Invalid confirm action")

    def _sync_ingredient_family(self, ingredient: Ingredient) -> None:
        if not ingredient.family:
            ingredient.family_id = None
            return
        try:
            family_id, food_group_id = resolve_family_fields(
                self.db,
                family=ingredient.family,
                family_id=ingredient.family_id,
            )
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc
        ingredient.family = family_id
        ingredient.family_id = family_id
        if food_group_id and not ingredient.food_group:
            ingredient.food_group = food_group_id

    def create_ingredient(self, payload: IngredientCreateRequest) -> Ingredient:
        canonical = normalize_name(payload.canonical_name)
        if self.db.scalar(select(Ingredient).where(func.lower(Ingredient.canonical_name) == canonical)):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ingredient already exists")
        ingredient = Ingredient(
            canonical_name=canonical,
            display_name=payload.display_name,
            category=payload.category,
            food_group=payload.food_group
            or food_group_for_ingredient(
                food_group=None,
                category=payload.category,
                family=payload.family,
            ),
            family=payload.family,
            storage_class=payload.storage_class,
            culinary_category=payload.culinary_category,
            product_form=payload.product_form,
            preservation=payload.preservation,
            default_unit_id=payload.default_unit_id,
            default_dimension=payload.default_dimension,
            preferred_shopping_unit_id=payload.preferred_shopping_unit_id,
            aggregation_unit_id=payload.aggregation_unit_id,
            aggregation_strategy=payload.aggregation_strategy,
            pantry_item=payload.pantry_item,
            season_start_month=payload.season_start_month,
            season_end_month=payload.season_end_month,
            notes=payload.notes,
        )
        if payload.family:
            self._sync_ingredient_family(ingredient)
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
        updates = payload.model_dump(exclude_unset=True)
        trait_fields = {"category", "food_group", "family", "family_id", "pantry_item"}
        for field, value in updates.items():
            setattr(ingredient, field, value)
        if "family" in updates and "family_id" not in updates:
            ingredient.family_id = None
        if "family" in updates or "family_id" in updates:
            self._sync_ingredient_family(ingredient)
        if "category" in updates or "food_group" in updates:
            ingredient.food_group = food_group_for_ingredient(
                food_group=ingredient.food_group,
                category=ingredient.category,
                family=ingredient.family,
            )
        self.db.commit()
        self.db.refresh(ingredient)
        if trait_fields.intersection(updates.keys()):
            self._refresh_recipes_for_ingredient(ingredient.id)
            self.db.commit()
        return ingredient

    def delete_ingredient(self, ingredient_id: int) -> None:
        ingredient = self.get_ingredient(ingredient_id)
        self.db.delete(ingredient)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ingredient is still referenced by one or more recipes",
            ) from exc

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

    def list_conversions(self, ingredient_id: int) -> list[IngredientUnitConversion]:
        self.get_ingredient(ingredient_id)
        return list(
            self.db.scalars(
                select(IngredientUnitConversion)
                .options(
                    selectinload(IngredientUnitConversion.from_unit),
                    selectinload(IngredientUnitConversion.to_unit),
                )
                .where(IngredientUnitConversion.ingredient_id == ingredient_id)
                .order_by(IngredientUnitConversion.from_unit_id, IngredientUnitConversion.to_unit_id)
            )
        )

    def create_conversion(
        self,
        ingredient_id: int,
        payload: IngredientUnitConversionCreateRequest,
    ) -> IngredientUnitConversion:
        ingredient = self.get_ingredient(ingredient_id)
        self.get_unit(payload.from_unit_id)
        self.get_unit(payload.to_unit_id)
        existing = self.db.scalar(
            select(IngredientUnitConversion).where(
                IngredientUnitConversion.ingredient_id == ingredient.id,
                IngredientUnitConversion.from_unit_id == payload.from_unit_id,
                IngredientUnitConversion.to_unit_id == payload.to_unit_id,
            )
        )
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conversion already exists")
        conversion = IngredientUnitConversion(
            ingredient_id=ingredient.id,
            from_unit_id=payload.from_unit_id,
            to_unit_id=payload.to_unit_id,
            factor=payload.factor,
            confidence=payload.confidence,
            notes=payload.notes,
            approved=payload.approved,
            source=payload.source,
        )
        self.db.add(conversion)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conversion already exists") from None
        self.db.refresh(conversion)
        loaded = self.db.scalar(
            select(IngredientUnitConversion)
            .options(
                selectinload(IngredientUnitConversion.from_unit),
                selectinload(IngredientUnitConversion.to_unit),
            )
            .where(IngredientUnitConversion.id == conversion.id)
        )
        if loaded is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to load conversion after create",
            )
        if loaded.approved:
            self._refresh_recipes_for_ingredient(loaded.ingredient_id)
            self.db.commit()
        return loaded

    def update_conversion(
        self,
        conversion_id: int,
        payload: IngredientUnitConversionUpdateRequest,
    ) -> IngredientUnitConversion:
        conversion = self.db.scalar(
            select(IngredientUnitConversion)
            .options(
                selectinload(IngredientUnitConversion.from_unit),
                selectinload(IngredientUnitConversion.to_unit),
            )
            .where(IngredientUnitConversion.id == conversion_id)
        )
        if conversion is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversion not found")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(conversion, field, value)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conversion already exists") from None
        self.db.refresh(conversion)
        if {"factor", "approved"}.intersection(payload.model_dump(exclude_unset=True).keys()):
            self._refresh_recipes_for_ingredient(conversion.ingredient_id)
            self.db.commit()
        return conversion

    def delete_conversion(self, conversion_id: int) -> None:
        conversion = self.db.get(IngredientUnitConversion, conversion_id)
        if conversion is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversion not found")
        ingredient_id = conversion.ingredient_id
        self.db.delete(conversion)
        self.db.commit()
        self._refresh_recipes_for_ingredient(ingredient_id)
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
        if payload.seasonality_mode == SeasonalityMode.all_year:
            dish.seasonality.preferred_months = []
        else:
            dish.seasonality.preferred_months = payload.preferred_months
        dish.seasonality.allowed_months = []
        dish.seasonality.excluded_months = []
        dish.seasonality.seasonality_strength = SeasonalityStrength.neutral

    def _dish_query_options(self):
        return (
            selectinload(Dish.tags),
            selectinload(Dish.seasonality),
            selectinload(Dish.recipes)
            .selectinload(Recipe.ingredients)
            .selectinload(RecipeIngredient.ingredient)
            .selectinload(Ingredient.unit_conversions),
            selectinload(Dish.recipes).selectinload(Recipe.ingredients).selectinload(RecipeIngredient.unit),
        )

    def list_dishes(self, active_only: bool = False) -> list[Dish]:
        query = (
            select(Dish)
            .where(Dish.household_id == self.household_id)
            .options(*self._dish_query_options())
            .order_by(Dish.name)
        )
        if active_only:
            query = query.where(Dish.status == DishStatus.active)
        return list(self.db.scalars(query))

    def get_dish(self, dish_id: int) -> Dish:
        dish = self.db.scalar(
            select(Dish)
            .where(Dish.id == dish_id, Dish.household_id == self.household_id)
            .options(*self._dish_query_options())
        )
        if dish is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dish not found")
        return dish

    def create_dish(self, payload: DishCreateRequest) -> Dish:
        if self.db.scalar(
            select(Dish).where(Dish.name == payload.name, Dish.household_id == self.household_id)
        ):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Dish already exists")
        for attempt in range(5):
            dish = Dish(
                household_id=self.household_id,
                public_key=self._generate_unique_dish_public_key(payload.name),
                name=payload.name,
                description=payload.description,
                default_servings=payload.default_servings,
                course=payload.course,
                meal_composition=payload.meal_composition,
                simple_dish_part=payload.simple_dish_part,
                status=payload.status,
                image_url=payload.image_url,
                suitable_for_lunch=payload.suitable_for_lunch,
                suitable_for_dinner=payload.suitable_for_dinner,
                weekday_friendly=payload.weekday_friendly,
                leftovers_possible=payload.leftovers_possible,
                freezer_friendly=payload.freezer_friendly,
                kids_friendly=payload.kids_friendly,
                active=payload.status == DishStatus.active,
                notes=payload.notes,
            )
            self.db.add(dish)
            self.db.flush()
            self._apply_tags(dish, payload.tag_ids)
            self._apply_seasonality(dish, payload.seasonality)
            try:
                self.db.commit()
                self.db.refresh(dish)
                return self.get_dish(dish.id)
            except IntegrityError:
                self.db.rollback()
                if attempt == 4:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Could not generate unique dish public key",
                    ) from None
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not generate unique dish public key",
        )

    def update_dish(self, dish_id: int, payload: DishUpdateRequest) -> Dish:
        dish = self.get_dish(dish_id)
        updates = payload.model_dump(
            exclude_unset=True,
            exclude={"tag_ids", "seasonality", "active", *self._INHERITED_DISH_FIELDS},
        )
        for field, value in updates.items():
            setattr(dish, field, value)
        if "meal_composition" in payload.model_fields_set and dish.meal_composition != MealComposition.simple_dish:
            dish.simple_dish_part = None
        if "simple_dish_part" in payload.model_fields_set and payload.simple_dish_part is None:
            if dish.meal_composition == MealComposition.simple_dish:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail="simple_dish_part is required when meal_composition is simple_dish",
                )
        self._validate_dish_meal_composition(dish)
        if "status" in payload.model_fields_set:
            dish.active = dish.status == DishStatus.active
        if "active" in payload.model_fields_set and payload.active is not None:
            dish.status = DishStatus.active if payload.active else DishStatus.archived
            dish.active = payload.active
        if "tag_ids" in payload.model_fields_set:
            self._apply_tags(dish, payload.tag_ids or [])
        if "seasonality" in payload.model_fields_set:
            self._apply_seasonality(dish, payload.seasonality)
        self.db.commit()
        return self.get_dish(dish.id)

    def delete_dish(self, dish_id: int) -> None:
        dish = self.get_dish(dish_id)
        self.db.delete(dish)
        self.db.commit()

    def list_recipes(self, dish_id: int) -> list[Recipe]:
        self.get_dish(dish_id)
        return list(
            self.db.scalars(
                select(Recipe)
                .where(Recipe.dish_id == dish_id)
                .options(
                    selectinload(Recipe.ingredients)
                    .selectinload(RecipeIngredient.ingredient)
                    .selectinload(Ingredient.unit_conversions),
                    selectinload(Recipe.ingredients).selectinload(RecipeIngredient.unit),
                )
                .order_by(Recipe.is_main.desc(), Recipe.id)
            )
        )

    def get_recipe(self, recipe_id: int) -> Recipe:
        recipe = self.db.scalar(
            select(Recipe)
            .join(Dish, Recipe.dish_id == Dish.id)
            .where(Recipe.id == recipe_id, Dish.household_id == self.household_id)
        )
        if recipe is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
        return recipe

    def get_recipe_by_public_key(self, public_key: str) -> Recipe:
        recipe = self.db.scalar(
            select(Recipe)
            .join(Dish, Recipe.dish_id == Dish.id)
            .where(Recipe.public_key == public_key, Dish.household_id == self.household_id)
        )
        if recipe is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
        return recipe

    def create_recipe(self, dish_id: int, payload: RecipeCreateRequest) -> Recipe:
        dish = self.get_dish(dish_id)
        if self.db.scalar(
            select(Recipe).where(Recipe.dish_id == dish_id, Recipe.variant_name == payload.variant_name)
        ):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Recipe variant already exists")
        is_main = payload.is_main if payload.is_main is not None else len(dish.recipes) == 0
        data = payload.model_dump(exclude={"is_thermomix", "is_main"})
        recipe_type = self._resolve_recipe_type(payload.recipe_type, payload.is_thermomix)

        for attempt in range(5):
            if is_main:
                for existing in dish.recipes:
                    existing.is_main = False
            sequence_number = self._next_recipe_sequence_number(dish_id)
            recipe = Recipe(
                dish_id=dish_id,
                public_key=self._recipe_public_key(dish, sequence_number),
                sequence_number=sequence_number,
                is_main=is_main,
                computed_traits_json={},
                **data,
            )
            self._apply_recipe_type(recipe, recipe_type)
            self.db.add(recipe)
            try:
                self.db.flush()
                self._refresh_recipe_traits(recipe)
                self.db.commit()
                self.db.refresh(recipe)
                return recipe
            except IntegrityError:
                self.db.rollback()
                dish = self.get_dish(dish_id)
                if attempt == 4:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Recipe sequence number conflict; retry the request",
                    ) from None
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Recipe sequence number conflict; retry the request",
        )

    def update_recipe(self, recipe_id: int, payload: RecipeUpdateRequest) -> Recipe:
        recipe = self.get_recipe(recipe_id)
        updates = payload.model_dump(exclude_unset=True, exclude={"is_thermomix", "recipe_type", "is_main"})
        for field, value in updates.items():
            setattr(recipe, field, value)
        if "recipe_type" in payload.model_fields_set or "is_thermomix" in payload.model_fields_set:
            recipe_type = self._resolve_recipe_type(
                payload.recipe_type if "recipe_type" in payload.model_fields_set else None,
                payload.is_thermomix if "is_thermomix" in payload.model_fields_set else None,
                recipe.recipe_type,
            )
            self._apply_recipe_type(recipe, recipe_type)
        if "is_main" in payload.model_fields_set:
            if payload.is_main:
                self._set_main_recipe(recipe.dish_id, recipe.id)
            elif recipe.is_main:
                others = list(
                    self.db.scalars(
                        select(Recipe)
                        .where(Recipe.dish_id == recipe.dish_id, Recipe.id != recipe.id)
                        .order_by(Recipe.id)
                    )
                )
                if not others:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                        detail="Cannot unset main recipe when it is the only variant",
                    )
                recipe.is_main = False
                others[0].is_main = True
        self.db.commit()
        self.db.refresh(recipe)
        return recipe

    def delete_recipe(self, recipe_id: int) -> None:
        recipe = self.get_recipe(recipe_id)
        dish_id = recipe.dish_id
        was_main = recipe.is_main
        self.db.delete(recipe)
        self.db.flush()
        if was_main:
            next_main = self.db.scalar(
                select(Recipe).where(Recipe.dish_id == dish_id).order_by(Recipe.id).limit(1)
            )
            if next_main is not None:
                next_main.is_main = True
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
        self.get_recipe(step.recipe_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(step, field, value)
        self.db.commit()
        self.db.refresh(step)
        return step

    def delete_step(self, step_id: int) -> None:
        step = self.db.get(RecipeStep, step_id)
        if step is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe step not found")
        self.get_recipe(step.recipe_id)
        self.db.delete(step)
        self.db.commit()

    def _resolve_ingredient_id(self, ingredient_id: int | None, proposed_name: str | None) -> int:
        if ingredient_id is not None:
            self.get_ingredient(ingredient_id)
            return ingredient_id
        if proposed_name is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
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
        self.db.flush()
        self._refresh_recipe_traits(self.get_recipe(recipe_id))
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
        self._refresh_recipe_traits(self.get_recipe(item.recipe_id))
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete_recipe_ingredient(self, item_id: int) -> None:
        item = self.db.get(RecipeIngredient, item_id)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe ingredient not found")
        recipe = self.get_recipe(item.recipe_id)
        self.db.delete(item)
        self.db.flush()
        self._refresh_recipe_traits(recipe)
        self.db.commit()
