"""Import dish/recipe fixtures from YAML into the catalog."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import yaml
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from mealroulette.models.catalog import Dish, Tag, Unit
from mealroulette.models.enums import (
    DifficultyLevel,
    DishCourse,
    DishStatus,
    RecipeType,
    SeasonalityMode,
)
from mealroulette.schemas.catalog import (
    DishCreateRequest,
    IngredientConfirmAction,
    RecipeCreateRequest,
    RecipeIngredientCreateRequest,
    RecipeStepCreateRequest,
    SeasonalityUpsertRequest,
)
from mealroulette.data.seed_catalog import seed_ingredient_conversions
from mealroulette.services.catalog import CatalogService

FIXTURES_DIR = Path(__file__).parent / "fixtures"
DEFAULT_FIXTURE_PATH = FIXTURES_DIR / "sample_dishes.yaml"


@dataclass(frozen=True)
class ImportResult:
    dishes_added: int
    dishes_skipped: int
    recipes_added: int
    steps_added: int
    ingredients_added: int
    ingredients_created: int

    @property
    def total_added(self) -> int:
        return self.dishes_added + self.recipes_added + self.steps_added + self.ingredients_added


def load_fixture(path: Path | str) -> dict:
    fixture_path = Path(path)
    with fixture_path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict) or "dishes" not in data:
        raise ValueError(f"Invalid fixture file: {fixture_path}")
    return data


def _parse_tag_specs(raw: list | None) -> list[tuple[str, str]]:
    if not raw:
        return []
    specs: list[tuple[str, str]] = []
    for item in raw:
        if not isinstance(item, dict) or len(item) != 1:
            raise ValueError(f"Invalid tag entry: {item!r}")
        family, name = next(iter(item.items()))
        specs.append((str(family), str(name)))
    return specs


def _build_lookup_maps(db: Session) -> tuple[dict[str, int], dict[tuple[str, str], int]]:
    units = {unit.symbol: unit.id for unit in db.scalars(select(Unit))}
    tags = {(tag.family, tag.name): tag.id for tag in db.scalars(select(Tag))}
    return units, tags


def _resolve_tag_ids(tag_specs: list[tuple[str, str]], tag_lookup: dict[tuple[str, str], int]) -> list[int]:
    tag_ids: list[int] = []
    for family, name in tag_specs:
        key = (family, name)
        if key not in tag_lookup:
            raise ValueError(f"Unknown tag: {family}:{name}")
        tag_ids.append(tag_lookup[key])
    return tag_ids


def _get_or_create_ingredient(
    service: CatalogService,
    *,
    name: str,
    default_unit_id: int | None,
    created_count: list[int],
) -> int:
    resolved = service.resolve_ingredient(name)
    if resolved.status == "exact" and resolved.ingredient is not None:
        return resolved.ingredient.id

    try:
        ingredient = service.confirm_ingredient(
            action=IngredientConfirmAction.create,
            proposed_name=name,
            display_name=name.strip(),
            default_unit_id=default_unit_id,
        )
    except HTTPException as exc:
        if exc.status_code == 409:
            resolved = service.resolve_ingredient(name)
            if resolved.ingredient is not None:
                return resolved.ingredient.id
        raise ValueError(f"Could not create ingredient '{name}': {exc.detail}") from exc

    created_count[0] += 1
    return ingredient.id


def import_dish_fixtures(db: Session, path: Path | str = DEFAULT_FIXTURE_PATH) -> ImportResult:
    """Import dishes from a YAML fixture. Skips dishes that already exist by name."""
    data = load_fixture(path)
    service = CatalogService(db)
    unit_lookup, tag_lookup = _build_lookup_maps(db)

    dishes_added = 0
    dishes_skipped = 0
    recipes_added = 0
    steps_added = 0
    ingredients_added = 0
    ingredients_created = [0]

    for dish_data in data["dishes"]:
        dish_name = dish_data["name"]
        if db.scalar(select(Dish).where(func.lower(Dish.name) == dish_name.strip().lower())):
            dishes_skipped += 1
            continue

        tag_ids = _resolve_tag_ids(_parse_tag_specs(dish_data.get("tags")), tag_lookup)
        seasonality_raw = dish_data.get("seasonality")
        seasonality = None
        if seasonality_raw:
            seasonality = SeasonalityUpsertRequest(
                seasonality_mode=SeasonalityMode(seasonality_raw["seasonality_mode"]),
                preferred_months=seasonality_raw.get("preferred_months") or [],
            )

        dish = service.create_dish(
            DishCreateRequest(
                name=dish_name,
                description=dish_data.get("description"),
                course=DishCourse(dish_data["course"]) if dish_data.get("course") else None,
                status=DishStatus(dish_data.get("status", "active")),
                suitable_for_lunch=dish_data.get("suitable_for_lunch"),
                suitable_for_dinner=dish_data.get("suitable_for_dinner"),
                weekday_friendly=dish_data.get("weekday_friendly"),
                leftovers_possible=dish_data.get("leftovers_possible"),
                freezer_friendly=dish_data.get("freezer_friendly"),
                kids_friendly=dish_data.get("kids_friendly"),
                tag_ids=tag_ids,
                seasonality=seasonality,
            )
        )
        dishes_added += 1

        for recipe_data in dish_data.get("recipes") or []:
            recipe = service.create_recipe(
                dish.id,
                RecipeCreateRequest(
                    variant_name=recipe_data["variant_name"],
                    description=recipe_data.get("description"),
                    recipe_type=RecipeType(recipe_data.get("recipe_type", "standard")),
                    is_main=recipe_data.get("is_main"),
                    source_url=recipe_data.get("source_url"),
                    servings=recipe_data.get("servings"),
                    prep_time_minutes=recipe_data.get("prep_time_minutes"),
                    cook_time_minutes=recipe_data.get("cook_time_minutes"),
                    difficulty=DifficultyLevel(recipe_data["difficulty"])
                    if recipe_data.get("difficulty")
                    else None,
                    notes=recipe_data.get("notes"),
                ),
            )
            recipes_added += 1

            for step_data in recipe_data.get("steps") or []:
                service.create_step(
                    recipe.id,
                    RecipeStepCreateRequest(
                        step_number=step_data["step_number"],
                        instruction=step_data["instruction"],
                        duration_seconds=step_data.get("duration_seconds"),
                        temperature=step_data.get("temperature"),
                        timer_seconds=step_data.get("timer_seconds"),
                        is_thermomix_step=step_data.get("is_thermomix_step", False),
                        metadata_json=step_data.get("metadata_json"),
                    ),
                )
                steps_added += 1

            for ingredient_data in recipe_data.get("ingredients") or []:
                unit_symbol = ingredient_data.get("unit")
                unit_id = unit_lookup.get(unit_symbol) if unit_symbol else None
                if unit_symbol and unit_id is None:
                    raise ValueError(f"Unknown unit symbol: {unit_symbol}")

                ingredient_id = _get_or_create_ingredient(
                    service,
                    name=ingredient_data["name"],
                    default_unit_id=unit_id,
                    created_count=ingredients_created,
                )
                quantity = ingredient_data.get("quantity")
                service.add_recipe_ingredient(
                    recipe.id,
                    RecipeIngredientCreateRequest(
                        ingredient_id=ingredient_id,
                        quantity=Decimal(str(quantity)) if quantity is not None else None,
                        unit_id=unit_id,
                        optional=ingredient_data.get("optional", False),
                        notes=ingredient_data.get("notes"),
                    ),
                )
                ingredients_added += 1

    conversions_added = seed_ingredient_conversions(db)
    if conversions_added:
        db.commit()

    return ImportResult(
        dishes_added=dishes_added,
        dishes_skipped=dishes_skipped,
        recipes_added=recipes_added,
        steps_added=steps_added,
        ingredients_added=ingredients_added,
        ingredients_created=ingredients_created[0],
    )
