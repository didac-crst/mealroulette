from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from mealroulette.models.catalog import Dish, Ingredient, Recipe, RecipeIngredient, Unit
from mealroulette.models.enums import DishStatus, MealComposition, MealPlanItemStatus, SeasonalityMode
from mealroulette.models.planning import MealPlan, MealPlanItem, MealReview
from mealroulette.schemas.scheduler import PlanningRulesConfig
from mealroulette.services.recipe_traits import compute_recipe_traits_now
from mealroulette.services.quantities import UnitInfo
from mealroulette.services.scheduler.family_vector import build_family_vector_for_dish_main_recipe, unit_info_from_model
from mealroulette.services.scheduler.pair_diagnostics import (
    CandidatePairSummary,
    build_recipe_pair_diagnostics,
)
from mealroulette.services.scheduler.types import DishCandidate, EatenMealSnapshot


def load_reference_units(db: Session) -> tuple[UnitInfo, UnitInfo]:
    gram = db.scalar(select(Unit).where(Unit.symbol == "g"))
    milliliter = db.scalar(select(Unit).where(Unit.symbol == "ml"))
    if gram is None or milliliter is None:
        raise RuntimeError("Reference units g and ml must be seeded")
    return unit_info_from_model(gram), unit_info_from_model(milliliter)


def load_average_ratings(db: Session, *, household_id: UUID) -> dict[int, float]:
    rows = db.execute(
        select(MealReview.dish_id, func.avg(MealReview.rating))
        .join(Dish, MealReview.dish_id == Dish.id)
        .where(Dish.household_id == household_id)
        .group_by(MealReview.dish_id)
    )
    return {dish_id: float(avg) for dish_id, avg in rows.all() if avg is not None}


def load_dish_candidates(db: Session, *, rules: PlanningRulesConfig, household_id: UUID) -> list[DishCandidate]:
    gram_unit, ml_unit = load_reference_units(db)
    ratings = load_average_ratings(db, household_id=household_id)
    dishes = db.scalars(
        select(Dish)
        .where(Dish.status == DishStatus.active, Dish.household_id == household_id)
        .options(
            selectinload(Dish.tags),
            selectinload(Dish.seasonality),
            selectinload(Dish.recipes)
            .selectinload(Recipe.ingredients)
            .selectinload(RecipeIngredient.ingredient)
            .selectinload(Ingredient.unit_conversions),
            selectinload(Dish.recipes).selectinload(Recipe.ingredients).selectinload(RecipeIngredient.unit),
            selectinload(Dish.recipes).selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient),
        )
    ).all()

    candidates: list[DishCandidate] = []
    for dish in dishes:
        if dish.meal_composition == MealComposition.dessert:
            continue
        main_recipe = next((recipe for recipe in dish.recipes if recipe.is_main), None)
        if main_recipe is None:
            main_recipe = dish.recipes[0] if dish.recipes else None
        if main_recipe is None:
            continue

        vector_result = build_family_vector_for_dish_main_recipe(
            dish.recipes,
            gram_unit=gram_unit,
            ml_unit=ml_unit,
            vector_min_grams=rules.vector_min_grams,
            default_grams_per_count=rules.default_grams_per_count,
        )
        seasonality = dish.seasonality
        tag_names = frozenset(tag.name for tag in dish.tags)
        traits = compute_recipe_traits_now(
            db,
            main_recipe,
            gram_unit=gram_unit,
            ml_unit=ml_unit,
        )
        pair_summary: CandidatePairSummary | None = None
        if dish.meal_composition == MealComposition.simple_dish:
            diagnostics = build_recipe_pair_diagnostics(
                main_recipe,
                gram_unit=gram_unit,
                ml_unit=ml_unit,
                traits=traits,
                simple_dish_part=dish.simple_dish_part,
                tag_names=tag_names,
                vector_min_grams=rules.vector_min_grams,
                default_grams_per_count=rules.default_grams_per_count,
            )
            pair_summary = CandidatePairSummary(
                primary_ingredient_ids=diagnostics.primary_ingredient_ids,
                primary_family_keys=diagnostics.primary_family_keys,
                semantic_role=diagnostics.semantic_role,
            )
        candidates.append(
            DishCandidate(
                dish_id=dish.id,
                dish_name=dish.name,
                recipe_id=main_recipe.id,
                meal_composition=dish.meal_composition,
                simple_dish_part=dish.simple_dish_part,
                tag_names=tag_names,
                protein_tags=frozenset(tag.name for tag in dish.tags if tag.family == "protein"),
                carb_tags=frozenset(tag.name for tag in dish.tags if tag.family == "carb"),
                style_tags=frozenset(tag.name for tag in dish.tags if tag.family == "style"),
                vector=vector_result.weights,
                computed_traits_json=traits,
                pair_summary=pair_summary,
                average_rating=ratings.get(dish.id),
                seasonality_mode=seasonality.seasonality_mode if seasonality else SeasonalityMode.all_year,
                preferred_months=frozenset(seasonality.preferred_months if seasonality else []),
                suitable_for_lunch=dish.suitable_for_lunch,
                suitable_for_dinner=dish.suitable_for_dinner,
            )
        )
    return candidates


def load_eaten_meal_snapshots(
    db: Session,
    *,
    before_date: date,
    window_days: int,
    rules: PlanningRulesConfig,
    household_id: UUID,
) -> list[EatenMealSnapshot]:
    gram_unit, ml_unit = load_reference_units(db)
    earliest = before_date - timedelta(days=window_days)
    items = db.scalars(
        select(MealPlanItem)
        .join(MealPlan, MealPlanItem.meal_plan_id == MealPlan.id)
        .where(
            MealPlan.household_id == household_id,
            MealPlanItem.status == MealPlanItemStatus.eaten,
            MealPlanItem.date >= earliest,
            MealPlanItem.date < before_date,
            MealPlanItem.dish_id.is_not(None),
        )
        .options(
            selectinload(MealPlanItem.dish)
            .selectinload(Dish.recipes)
            .selectinload(Recipe.ingredients)
            .selectinload(RecipeIngredient.ingredient)
            .selectinload(Ingredient.unit_conversions),
            selectinload(MealPlanItem.dish)
            .selectinload(Dish.recipes)
            .selectinload(Recipe.ingredients)
            .selectinload(RecipeIngredient.unit),
        )
    ).all()

    snapshots: list[EatenMealSnapshot] = []
    for item in items:
        if item.dish is None:
            continue
        vector = build_family_vector_for_dish_main_recipe(
            item.dish.recipes,
            gram_unit=gram_unit,
            ml_unit=ml_unit,
            vector_min_grams=rules.vector_min_grams,
            default_grams_per_count=rules.default_grams_per_count,
        ).weights
        snapshots.append(
            EatenMealSnapshot(
                dish_id=item.dish_id,
                dish_name=item.dish.name,
                meal_date=item.date,
                vector=vector,
            )
        )
    return snapshots
