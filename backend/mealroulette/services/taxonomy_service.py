from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from mealroulette.models.catalog import Ingredient, IngredientAlias, IngredientUnitConversion
from mealroulette.models.taxonomy import FoodGroup, IngredientFamily
from mealroulette.schemas.taxonomy import (
    FoodGroupOverview,
    FoodGroupPublic,
    IngredientFamilyPublic,
    IngredientTaxonomyOverview,
    IngredientTaxonomySummary,
)


class TaxonomyService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _family_ids(self) -> set[str]:
        return set(self.db.scalars(select(IngredientFamily.id)))

    def list_food_groups(self) -> list[FoodGroupPublic]:
        rows = self.db.scalars(select(FoodGroup).order_by(FoodGroup.label)).all()
        return [
            FoodGroupPublic(id=row.id, label=row.label, description=row.description or "")
            for row in rows
        ]

    def list_families(self, *, food_group_id: str | None = None) -> list[IngredientFamilyPublic]:
        query = select(IngredientFamily).order_by(IngredientFamily.label)
        if food_group_id is not None:
            normalized = food_group_id.strip().lower()
            query = query.where(IngredientFamily.food_group_id == normalized)
        rows = self.db.scalars(query).all()
        return [
            IngredientFamilyPublic(
                id=row.id,
                food_group=row.food_group_id,
                label=row.label,
                description=row.description or "",
            )
            for row in rows
        ]

    def list_ingredients_for_family(self, family_id: str) -> list[IngredientTaxonomySummary]:
        family_ids = self._family_ids()
        normalized = family_id.strip().lower()
        ingredients = self.db.scalars(
            select(Ingredient)
            .where(
                or_(
                    Ingredient.family_id == normalized,
                    func.lower(Ingredient.family) == normalized,
                )
            )
            .options(
                selectinload(Ingredient.aliases),
                selectinload(Ingredient.unit_conversions),
            )
            .order_by(Ingredient.display_name)
        ).all()
        return [self._summarize_ingredient(ingredient, family_ids) for ingredient in ingredients]

    def overview(self) -> IngredientTaxonomyOverview:
        ingredients = list(self.db.scalars(select(Ingredient)))
        alias_count = self.db.scalar(select(func.count()).select_from(IngredientAlias)) or 0
        approved = (
            self.db.scalar(
                select(func.count())
                .select_from(IngredientUnitConversion)
                .where(IngredientUnitConversion.approved.is_(True))
            )
            or 0
        )
        unapproved = (
            self.db.scalar(
                select(func.count())
                .select_from(IngredientUnitConversion)
                .where(IngredientUnitConversion.approved.is_(False))
            )
            or 0
        )

        families = list(self.db.scalars(select(IngredientFamily)))
        family_ids = {family.id for family in families}
        group_rows: dict[str, FoodGroupOverview] = {}

        for group in self.db.scalars(select(FoodGroup).order_by(FoodGroup.label)):
            group_rows[group.id] = FoodGroupOverview(
                id=group.id,
                label=group.label,
                family_count=sum(1 for family in families if family.food_group_id == group.id),
                ingredient_count=0,
                missing_metadata_count=0,
            )

        for ingredient in ingredients:
            group_id = (ingredient.food_group or "other").strip().lower()
            if group_id not in group_rows:
                group_rows[group_id] = FoodGroupOverview(
                    id=group_id,
                    label=group_id,
                    family_count=0,
                    ingredient_count=0,
                    missing_metadata_count=0,
                )
            group_rows[group_id].ingredient_count += 1
            if self._is_missing_family(ingredient, family_ids) or not ingredient.food_group:
                group_rows[group_id].missing_metadata_count += 1

        return IngredientTaxonomyOverview(
            totals={
                "food_groups": len(group_rows),
                "families": len(families),
                "ingredients": len(ingredients),
                "aliases": int(alias_count),
                "approved_conversions": int(approved),
                "unapproved_conversions": int(unapproved),
            },
            food_groups=sorted(group_rows.values(), key=lambda row: row.label),
        )

    @staticmethod
    def _is_missing_family(ingredient: Ingredient, family_ids: set[str]) -> bool:
        if ingredient.family_id:
            return False
        if not ingredient.family:
            return True
        return ingredient.family not in family_ids

    def _summarize_ingredient(self, ingredient: Ingredient, family_ids: set[str]) -> IngredientTaxonomySummary:
        approved = sum(1 for conversion in ingredient.unit_conversions if conversion.approved)
        unapproved = sum(1 for conversion in ingredient.unit_conversions if not conversion.approved)
        return IngredientTaxonomySummary(
            id=ingredient.id,
            canonical_name=ingredient.canonical_name,
            display_name=ingredient.display_name,
            food_group=ingredient.food_group,
            family=ingredient.family_id or ingredient.family,
            pantry_item=ingredient.pantry_item,
            alias_count=len(ingredient.aliases),
            approved_conversion_count=approved,
            unapproved_conversion_count=unapproved,
            missing_family=self._is_missing_family(ingredient, family_ids),
            missing_food_group=not ingredient.food_group,
        )
