from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from mealroulette.models.catalog import Ingredient, IngredientUnitConversion, Recipe, RecipeIngredient, Unit
from mealroulette.models.enums import AggregationStrategy, MealPlanningState, MealPlanItemStatus, ShoppingListStatus
from mealroulette.models.planning import MealPlanItem, MealPlanItemDish
from mealroulette.models.shopping import ShoppingList, ShoppingListItem
from mealroulette.schemas.shopping import (
    ShoppingListCreateRequest,
    ShoppingListItemPublic,
    ShoppingListItemUpdateRequest,
    ShoppingListPublic,
    ShoppingPlannedMeal,
    ShoppingQuantityComponent,
    ShoppingSourceContribution,
    ShoppingSourceMeal,
)
from mealroulette.services.planning_rules import meal_slot_sort_key
from mealroulette.services.quantities import (
    AggregatedQuantity,
    IngredientConversion,
    QuantityLine,
    UnitInfo,
    aggregate_quantities,
    cross_dimension_mergeable,
    partition_merge_groups,
)


@dataclass(frozen=True)
class _IngredientAggregationContext:
    aggregation_strategy: AggregationStrategy | None
    preferred_display_unit: UnitInfo | None


@dataclass(frozen=True)
class _SourcedLine:
    line: QuantityLine
    meal_plan_item_id: int
    optional: bool
    dish_name: str
    recipe_variant_name: str | None


@dataclass(frozen=True)
class _GeneratedItem:
    ingredient_id: int
    display_name: str
    quantity: Decimal
    unit_id: int
    unit_symbol: str
    category: str
    approximate: bool
    optional: bool
    source_meal_plan_item_ids: list[int]
    source_meals: list[ShoppingSourceMeal]
    source_contributions: list[ShoppingSourceContribution]
    raw_components: list[ShoppingQuantityComponent]


class ShoppingListService:
    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def _window_end(from_date: date, days: int) -> date:
        return from_date + timedelta(days=days - 1)

    @staticmethod
    def _category_name(ingredient: Ingredient) -> str:
        if ingredient.category and ingredient.category.strip():
            return ingredient.category.strip()
        return "Other"

    def _load_units(self) -> dict[int, UnitInfo]:
        return {
            unit.id: UnitInfo(
                id=unit.id,
                symbol=unit.symbol,
                dimension=unit.dimension,
                conversion_to_base=unit.conversion_to_base,
            )
            for unit in self.db.scalars(select(Unit))
        }

    def _load_conversions(self, ingredient_ids: set[int]) -> dict[int, list[IngredientConversion]]:
        if not ingredient_ids:
            return {}
        rows = self.db.scalars(
            select(IngredientUnitConversion).where(
                IngredientUnitConversion.ingredient_id.in_(ingredient_ids),
                IngredientUnitConversion.approved.is_(True),
            )
        )
        grouped: dict[int, list[IngredientConversion]] = {}
        for row in rows:
            grouped.setdefault(row.ingredient_id, []).append(
                IngredientConversion(
                    from_unit_id=row.from_unit_id,
                    to_unit_id=row.to_unit_id,
                    factor=row.factor,
                )
            )
        return grouped

    def _eligible_meal_items(self, from_date: date, to_date: date) -> list[MealPlanItem]:
        recipe_ingredient_load = (
            selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient),
            selectinload(Recipe.ingredients).selectinload(RecipeIngredient.unit),
        )
        items = list(
            self.db.scalars(
                select(MealPlanItem)
                .where(
                    MealPlanItem.date >= from_date,
                    MealPlanItem.date <= to_date,
                    MealPlanItem.status == MealPlanItemStatus.planned,
                    MealPlanItem.planning_state != MealPlanningState.do_not_plan,
                )
                .options(
                    selectinload(MealPlanItem.dish),
                    selectinload(MealPlanItem.recipe).options(*recipe_ingredient_load),
                    selectinload(MealPlanItem.lines)
                    .selectinload(MealPlanItemDish.dish),
                    selectinload(MealPlanItem.lines)
                    .selectinload(MealPlanItemDish.recipe)
                    .options(*recipe_ingredient_load),
                )
                .order_by(MealPlanItem.date, MealPlanItem.meal_slot)
            )
        )
        return [
            item
            for item in items
            if any(line.recipe_id is not None for line in item.lines) or item.recipe_id is not None
        ]

    @staticmethod
    def _recipe_sources_for_item(meal_item: MealPlanItem) -> list[tuple[Recipe, str | None, str | None]]:
        sources: list[tuple[Recipe, str | None, str | None]] = []
        for line in sorted(meal_item.lines, key=lambda row: row.position):
            if line.recipe is None:
                continue
            dish_name = line.dish.name if line.dish else "Unknown"
            recipe_variant_name = line.recipe.variant_name if line.recipe else None
            sources.append((line.recipe, dish_name, recipe_variant_name))
        if not sources and meal_item.recipe is not None:
            dish_name = meal_item.dish.name if meal_item.dish else "Unknown"
            recipe_variant_name = meal_item.recipe.variant_name if meal_item.recipe else None
            sources.append((meal_item.recipe, dish_name, recipe_variant_name))
        return sources

    def _collect_sourced_lines(
        self,
        meal_items: list[MealPlanItem],
        units: dict[int, UnitInfo],
        exclude_pantry: bool,
    ) -> list[_SourcedLine]:
        sourced: list[_SourcedLine] = []
        for meal_item in meal_items:
            for recipe, dish_name, recipe_variant_name in self._recipe_sources_for_item(meal_item):
                for recipe_ingredient in recipe.ingredients:
                    ingredient = recipe_ingredient.ingredient
                    if exclude_pantry and ingredient.pantry_item:
                        continue
                    if recipe_ingredient.quantity is None or recipe_ingredient.unit_id is None:
                        continue
                    unit = units.get(recipe_ingredient.unit_id)
                    if unit is None:
                        continue
                    sourced.append(
                        _SourcedLine(
                            line=QuantityLine(
                                ingredient_id=ingredient.id,
                                quantity=recipe_ingredient.quantity,
                                unit=unit,
                            ),
                            meal_plan_item_id=meal_item.id,
                            optional=recipe_ingredient.optional,
                            dish_name=dish_name,
                            recipe_variant_name=recipe_variant_name,
                        )
                    )
        return sourced

    def _ingredient_contexts(
        self,
        ingredient_ids: set[int],
        units: dict[int, UnitInfo],
    ) -> dict[int, _IngredientAggregationContext]:
        if not ingredient_ids:
            return {}
        rows = self.db.scalars(select(Ingredient).where(Ingredient.id.in_(ingredient_ids)))
        contexts: dict[int, _IngredientAggregationContext] = {}
        for ingredient in rows:
            preferred_unit_id = ingredient.preferred_shopping_unit_id or ingredient.aggregation_unit_id
            preferred_display_unit = units.get(preferred_unit_id) if preferred_unit_id else None
            contexts[ingredient.id] = _IngredientAggregationContext(
                aggregation_strategy=ingredient.aggregation_strategy,
                preferred_display_unit=preferred_display_unit,
            )
        return contexts

    @staticmethod
    def _partition_merge_groups(
        ingredient_lines: list[_SourcedLine],
        conversions: list[IngredientConversion],
        aggregation_strategy: AggregationStrategy | None,
    ) -> list[list[_SourcedLine]]:
        return partition_merge_groups(
            ingredient_lines,
            lambda left, right: cross_dimension_mergeable(
                left.line.unit,
                right.line.unit,
                aggregation_strategy,
                conversions,
            ),
        )

    def _aggregate_sourced_lines(
        self,
        sourced: list[_SourcedLine],
        conversions_by_ingredient: dict[int, list[IngredientConversion]],
        ingredient_contexts: dict[int, _IngredientAggregationContext],
    ) -> list[tuple[AggregatedQuantity, list[_SourcedLine]]]:
        grouped: dict[int, list[_SourcedLine]] = {}
        for entry in sourced:
            grouped.setdefault(entry.line.ingredient_id, []).append(entry)

        results: list[tuple[AggregatedQuantity, list[_SourcedLine]]] = []
        for ingredient_id, ingredient_lines in grouped.items():
            conversions = conversions_by_ingredient.get(ingredient_id, [])
            context = ingredient_contexts.get(
                ingredient_id,
                _IngredientAggregationContext(aggregation_strategy=None, preferred_display_unit=None),
            )
            for merge_group in self._partition_merge_groups(
                ingredient_lines,
                conversions,
                context.aggregation_strategy,
            ):
                aggregated_rows = aggregate_quantities(
                    [entry.line for entry in merge_group],
                    conversions,
                    aggregation_strategy=context.aggregation_strategy,
                    preferred_display_unit=context.preferred_display_unit,
                )
                for aggregated in aggregated_rows:
                    contributing = [
                        entry
                        for entry in merge_group
                        if cross_dimension_mergeable(
                            entry.line.unit,
                            aggregated.unit,
                            context.aggregation_strategy,
                            conversions,
                        )
                    ]
                    results.append((aggregated, contributing))
        return results

    @staticmethod
    def _contributions_from_entries(
        entries: list[_SourcedLine],
        meal_by_id: dict[int, MealPlanItem],
    ) -> list[ShoppingSourceContribution]:
        contributions: list[ShoppingSourceContribution] = []
        for entry in entries:
            meal_item = meal_by_id[entry.meal_plan_item_id]
            contributions.append(
                ShoppingSourceContribution(
                    meal_plan_item_id=entry.meal_plan_item_id,
                    date=meal_item.date,
                    meal_slot=meal_item.meal_slot,
                    dish_name=entry.dish_name,
                    recipe_variant_name=entry.recipe_variant_name,
                    quantity=entry.line.quantity,
                    unit_symbol=entry.line.unit.symbol,
                    optional=entry.optional,
                )
            )
        contributions.sort(
            key=lambda item: (
                item.date,
                meal_slot_sort_key(item.meal_slot),
                item.dish_name.lower(),
            )
        )
        return contributions

    @staticmethod
    def _raw_components_from_contributions(
        contributions: list[ShoppingSourceContribution],
    ) -> list[ShoppingQuantityComponent]:
        totals: dict[str, Decimal] = {}
        for contribution in contributions:
            totals[contribution.unit_symbol] = totals.get(contribution.unit_symbol, Decimal("0")) + contribution.quantity
        return [
            ShoppingQuantityComponent(quantity=quantity, unit_symbol=unit_symbol)
            for unit_symbol, quantity in sorted(totals.items(), key=lambda item: item[0])
        ]

    @staticmethod
    def _source_meals_from_contributions(
        contributions: list[ShoppingSourceContribution],
    ) -> list[ShoppingSourceMeal]:
        seen: set[int] = set()
        meals: list[ShoppingSourceMeal] = []
        for contribution in contributions:
            if contribution.meal_plan_item_id in seen:
                continue
            seen.add(contribution.meal_plan_item_id)
            meals.append(
                ShoppingSourceMeal(
                    meal_plan_item_id=contribution.meal_plan_item_id,
                    date=contribution.date,
                    meal_slot=contribution.meal_slot,
                    dish_name=contribution.dish_name,
                    recipe_variant_name=contribution.recipe_variant_name,
                )
            )
        return meals

    @staticmethod
    def _build_planned_meals(meal_items: list[MealPlanItem]) -> list[ShoppingPlannedMeal]:
        planned: list[ShoppingPlannedMeal] = []
        for item in meal_items:
            for recipe, dish_name, recipe_variant_name in ShoppingListService._recipe_sources_for_item(item):
                planned.append(
                    ShoppingPlannedMeal(
                        meal_plan_item_id=item.id,
                        date=item.date,
                        meal_slot=item.meal_slot,
                        dish_name=dish_name,
                        recipe_variant_name=recipe_variant_name,
                    )
                )
        return planned

    @staticmethod
    def _contributions_to_json(contributions: list[ShoppingSourceContribution]) -> list[dict]:
        return [contribution.model_dump(mode="json") for contribution in contributions]

    @staticmethod
    def _contributions_from_json(data: list | None) -> list[ShoppingSourceContribution]:
        if not data:
            return []
        return [ShoppingSourceContribution.model_validate(row) for row in data]

    def _build_generated_items(
        self,
        meal_items: list[MealPlanItem],
        exclude_pantry: bool,
    ) -> list[_GeneratedItem]:
        units = self._load_units()
        sourced = self._collect_sourced_lines(meal_items, units, exclude_pantry)
        ingredient_ids = {entry.line.ingredient_id for entry in sourced}
        conversions_by_ingredient = self._load_conversions(ingredient_ids)
        ingredient_contexts = self._ingredient_contexts(ingredient_ids, units)

        meal_by_id = {item.id: item for item in meal_items}
        ingredient_cache: dict[int, Ingredient] = {}
        for meal_item in meal_items:
            for recipe, _, _ in self._recipe_sources_for_item(meal_item):
                for recipe_ingredient in recipe.ingredients:
                    ingredient_cache[recipe_ingredient.ingredient.id] = recipe_ingredient.ingredient

        generated: list[_GeneratedItem] = []
        for aggregated, group in self._aggregate_sourced_lines(
            sourced,
            conversions_by_ingredient,
            ingredient_contexts,
        ):
            ingredient = ingredient_cache[aggregated.ingredient_id]
            contributions = self._contributions_from_entries(group, meal_by_id)
            raw_components = self._raw_components_from_contributions(contributions)
            source_ids = sorted({entry.meal_plan_item_id for entry in group})
            source_meals = self._source_meals_from_contributions(contributions)
            generated.append(
                _GeneratedItem(
                    ingredient_id=aggregated.ingredient_id,
                    display_name=ingredient.display_name,
                    quantity=aggregated.quantity,
                    unit_id=aggregated.unit.id,
                    unit_symbol=aggregated.unit.symbol,
                    category=self._category_name(ingredient),
                    approximate=aggregated.approximate,
                    optional=any(entry.optional for entry in group),
                    source_meal_plan_item_ids=source_ids,
                    source_meals=source_meals,
                    source_contributions=contributions,
                    raw_components=raw_components,
                )
            )

        generated.sort(key=lambda item: (item.category.lower(), item.display_name.lower(), item.unit_symbol))
        return generated

    @classmethod
    def _to_item_public(
        cls,
        item: _GeneratedItem,
        *,
        row: ShoppingListItem | None = None,
        stored_contributions: list[ShoppingSourceContribution] | None = None,
    ) -> ShoppingListItemPublic:
        contributions = stored_contributions if stored_contributions is not None else item.source_contributions
        source_meals = cls._source_meals_from_contributions(contributions)
        raw_components = (
            item.raw_components
            if item.raw_components
            else cls._raw_components_from_contributions(contributions)
        )
        if row is not None:
            return ShoppingListItemPublic(
                id=row.id,
                ingredient_id=row.ingredient_id,
                display_name=row.display_name,
                quantity=row.quantity,
                unit_id=row.unit_id,
                unit_symbol=row.unit.symbol,
                category=row.category,
                checked=row.checked,
                approximate=row.approximate,
                optional=row.optional,
                source_meal_plan_item_ids=list(row.source_meal_plan_item_ids_json),
                source_meals=source_meals,
                source_contributions=contributions,
                raw_components=raw_components,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
        return ShoppingListItemPublic(
            ingredient_id=item.ingredient_id,
            display_name=item.display_name,
            quantity=item.quantity,
            unit_id=item.unit_id,
            unit_symbol=item.unit_symbol,
            category=item.category,
            checked=False,
            approximate=item.approximate,
            optional=item.optional,
            source_meal_plan_item_ids=item.source_meal_plan_item_ids,
            source_meals=source_meals,
            source_contributions=contributions,
            raw_components=raw_components,
        )

    def _list_public(
        self,
        *,
        from_date: date,
        to_date: date,
        exclude_pantry: bool,
        meal_items: list[MealPlanItem],
        generated: list[_GeneratedItem],
        rows: list[ShoppingListItem] | None = None,
        shopping_list: ShoppingList | None = None,
    ) -> ShoppingListPublic:
        if rows is not None and shopping_list is not None:
            items = [
                self._to_item_public(
                    gen,
                    row=row,
                    stored_contributions=self._contributions_from_json(row.source_contributions_json),
                )
                for gen, row in zip(generated, rows, strict=True)
            ]
            return ShoppingListPublic(
                id=shopping_list.id,
                from_date=shopping_list.from_date,
                to_date=shopping_list.to_date,
                status=shopping_list.status,
                exclude_pantry=shopping_list.exclude_pantry,
                items=items,
                planned_meals=self._build_planned_meals(meal_items),
                created_at=shopping_list.created_at,
                updated_at=shopping_list.updated_at,
            )

        return ShoppingListPublic(
            id=shopping_list.id if shopping_list else None,
            from_date=from_date,
            to_date=to_date,
            status=shopping_list.status if shopping_list else ShoppingListStatus.active,
            exclude_pantry=exclude_pantry,
            items=[self._to_item_public(item) for item in generated],
            planned_meals=self._build_planned_meals(meal_items),
            created_at=shopping_list.created_at if shopping_list else None,
            updated_at=shopping_list.updated_at if shopping_list else None,
        )

    def generate_preview(
        self,
        from_date: date,
        days: int,
        exclude_pantry: bool = True,
    ) -> ShoppingListPublic:
        to_date = self._window_end(from_date, days)
        meal_items = self._eligible_meal_items(from_date, to_date)
        generated = self._build_generated_items(meal_items, exclude_pantry)
        return self._list_public(
            from_date=from_date,
            to_date=to_date,
            exclude_pantry=exclude_pantry,
            meal_items=meal_items,
            generated=generated,
        )

    def create_list(self, payload: ShoppingListCreateRequest) -> ShoppingListPublic:
        to_date = self._window_end(payload.from_date, payload.days)
        meal_items = self._eligible_meal_items(payload.from_date, to_date)
        generated = self._build_generated_items(meal_items, payload.exclude_pantry)

        shopping_list = ShoppingList(
            from_date=payload.from_date,
            to_date=to_date,
            status=ShoppingListStatus.active,
            exclude_pantry=payload.exclude_pantry,
        )
        self.db.add(shopping_list)
        self.db.flush()

        item_rows: list[ShoppingListItem] = []
        for item in generated:
            row = ShoppingListItem(
                shopping_list_id=shopping_list.id,
                ingredient_id=item.ingredient_id,
                display_name=item.display_name,
                quantity=item.quantity,
                unit_id=item.unit_id,
                category=item.category,
                checked=False,
                approximate=item.approximate,
                optional=item.optional,
                source_meal_plan_item_ids_json=item.source_meal_plan_item_ids,
                source_contributions_json=self._contributions_to_json(item.source_contributions),
            )
            self.db.add(row)
            item_rows.append(row)

        self.db.commit()
        self.db.refresh(shopping_list)
        for row in item_rows:
            self.db.refresh(row)

        return self._list_public(
            from_date=shopping_list.from_date,
            to_date=shopping_list.to_date,
            exclude_pantry=shopping_list.exclude_pantry,
            meal_items=meal_items,
            generated=generated,
            rows=item_rows,
            shopping_list=shopping_list,
        )

    def get_list(self, shopping_list_id: int) -> ShoppingListPublic:
        shopping_list = self.db.scalar(
            select(ShoppingList)
            .where(ShoppingList.id == shopping_list_id)
            .options(
                selectinload(ShoppingList.items).selectinload(ShoppingListItem.unit),
                selectinload(ShoppingList.items).selectinload(ShoppingListItem.ingredient),
            )
        )
        if shopping_list is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shopping list not found")

        meal_item_ids: set[int] = set()
        for row in shopping_list.items:
            for contribution in self._contributions_from_json(row.source_contributions_json):
                meal_item_ids.add(contribution.meal_plan_item_id)
            meal_item_ids.update(row.source_meal_plan_item_ids_json)

        meal_items = list(
            self.db.scalars(
                select(MealPlanItem)
                .where(MealPlanItem.id.in_(meal_item_ids))
                .options(
                    selectinload(MealPlanItem.dish),
                    selectinload(MealPlanItem.recipe),
                    selectinload(MealPlanItem.lines).selectinload(MealPlanItemDish.dish),
                    selectinload(MealPlanItem.lines).selectinload(MealPlanItemDish.recipe),
                )
                .order_by(MealPlanItem.date, MealPlanItem.meal_slot)
            )
        ) if meal_item_ids else []

        generated: list[_GeneratedItem] = []
        for row in shopping_list.items:
            contributions = self._contributions_from_json(row.source_contributions_json)
            generated.append(
                _GeneratedItem(
                    ingredient_id=row.ingredient_id,
                    display_name=row.display_name,
                    quantity=row.quantity,
                    unit_id=row.unit_id,
                    unit_symbol=row.unit.symbol,
                    category=row.category,
                    approximate=row.approximate,
                    optional=row.optional,
                    source_meal_plan_item_ids=list(row.source_meal_plan_item_ids_json),
                    source_meals=self._source_meals_from_contributions(contributions),
                    source_contributions=contributions,
                    raw_components=[],
                )
            )

        return self._list_public(
            from_date=shopping_list.from_date,
            to_date=shopping_list.to_date,
            exclude_pantry=shopping_list.exclude_pantry,
            meal_items=meal_items,
            generated=generated,
            rows=list(shopping_list.items),
            shopping_list=shopping_list,
        )

    def update_item(self, item_id: int, payload: ShoppingListItemUpdateRequest) -> ShoppingListItemPublic:
        row = self.db.scalar(
            select(ShoppingListItem)
            .where(ShoppingListItem.id == item_id)
            .options(
                selectinload(ShoppingListItem.unit),
                selectinload(ShoppingListItem.ingredient),
            )
        )
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shopping list item not found")

        if payload.checked is not None:
            row.checked = payload.checked
        self.db.commit()
        self.db.refresh(row)

        contributions = self._contributions_from_json(row.source_contributions_json)
        generated = _GeneratedItem(
            ingredient_id=row.ingredient_id,
            display_name=row.display_name,
            quantity=row.quantity,
            unit_id=row.unit_id,
            unit_symbol=row.unit.symbol,
            category=row.category,
            approximate=row.approximate,
            optional=row.optional,
            source_meal_plan_item_ids=list(row.source_meal_plan_item_ids_json),
            source_meals=self._source_meals_from_contributions(contributions),
            source_contributions=contributions,
            raw_components=[],
        )
        return self._to_item_public(
            generated,
            row=row,
            stored_contributions=contributions,
        )
