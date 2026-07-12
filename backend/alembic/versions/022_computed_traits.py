"""Computed traits, public keys, and ingredient food groups.

Revision ID: 022_computed_traits
Revises: 021_meal_plan_roulette_undo
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session, selectinload

revision: str = "022_computed_traits"
down_revision: Union[str, Sequence[str], None] = "021_meal_plan_roulette_undo"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("ingredients", sa.Column("food_group", sa.String(length=64), nullable=True))
    op.add_column("dishes", sa.Column("public_key", sa.String(length=32), nullable=True))
    op.add_column("recipes", sa.Column("public_key", sa.String(length=36), nullable=True))
    op.add_column("recipes", sa.Column("sequence_number", sa.Integer(), nullable=True))
    op.add_column("recipes", sa.Column("computed_traits_json", JSONB(), nullable=True))

    bind = op.get_bind()
    session = Session(bind=bind)
    try:
        _backfill(session)
        session.flush()
    finally:
        session.close()

    op.alter_column("dishes", "public_key", nullable=False)
    op.alter_column("recipes", "public_key", nullable=False)
    op.alter_column("recipes", "sequence_number", nullable=False)
    op.create_unique_constraint("uq_dishes_public_key", "dishes", ["public_key"])
    op.create_unique_constraint("uq_recipes_public_key", "recipes", ["public_key"])
    op.create_unique_constraint("uq_recipes_dish_sequence", "recipes", ["dish_id", "sequence_number"])


def _ensure_reference_units(session: Session, load_reference_units) -> tuple:
    """Seed g/ml when missing so trait backfill works on databases without reference units."""
    from decimal import Decimal

    from sqlalchemy import select

    from mealroulette.models.catalog import Unit
    from mealroulette.models.enums import UnitDimension

    gram = session.scalar(select(Unit).where(Unit.symbol == "g"))
    if gram is None:
        gram = Unit(
            name="Gram",
            symbol="g",
            dimension=UnitDimension.mass,
            conversion_to_base=Decimal("1"),
        )
        session.add(gram)
    milliliter = session.scalar(select(Unit).where(Unit.symbol == "ml"))
    if milliliter is None:
        milliliter = Unit(
            name="Milliliter",
            symbol="ml",
            dimension=UnitDimension.volume,
            conversion_to_base=Decimal("1"),
        )
        session.add(milliliter)
    session.flush()
    return load_reference_units(session)


def _backfill(session: Session) -> None:
    from sqlalchemy import select

    from mealroulette.models.catalog import Dish, Ingredient, Recipe, RecipeIngredient
    from mealroulette.services.food_groups import food_group_for_ingredient
    from mealroulette.services.public_keys import generate_dish_public_key, generate_recipe_public_key
    from mealroulette.services.recipe_traits import refresh_recipe_traits
    from mealroulette.services.scheduler.catalog import load_reference_units

    ingredients = session.scalars(select(Ingredient)).all()
    for ingredient in ingredients:
        ingredient.food_group = food_group_for_ingredient(
            food_group=ingredient.food_group,
            category=ingredient.category,
        )

    existing_keys: set[str] = set()
    dishes = session.scalars(select(Dish).order_by(Dish.id)).all()
    for dish in dishes:
        for _ in range(20):
            candidate = generate_dish_public_key(dish.name)
            if candidate not in existing_keys:
                dish.public_key = candidate
                existing_keys.add(candidate)
                break
        else:
            raise RuntimeError(f"Could not generate unique public key for dish {dish.id}")

    if not dishes:
        return

    gram_unit, ml_unit = _ensure_reference_units(session, load_reference_units)

    for dish in dishes:
        recipes = list(
            session.scalars(
                select(Recipe)
                .where(Recipe.dish_id == dish.id)
                .options(
                    selectinload(Recipe.ingredients)
                    .selectinload(RecipeIngredient.ingredient)
                    .selectinload(Ingredient.unit_conversions),
                    selectinload(Recipe.ingredients).selectinload(RecipeIngredient.unit),
                )
            ).all()
        )
        mains = [recipe for recipe in recipes if recipe.is_main]
        main_recipe = min(mains, key=lambda recipe: recipe.id) if mains else None
        rest = sorted(
            [recipe for recipe in recipes if main_recipe is None or recipe.id != main_recipe.id],
            key=lambda recipe: recipe.id,
        )
        ordered = ([main_recipe] if main_recipe is not None else []) + rest
        for sequence, recipe in enumerate(ordered, start=1):
            recipe.sequence_number = sequence
            recipe.public_key = generate_recipe_public_key(dish.public_key, sequence)
            refresh_recipe_traits(session, recipe, gram_unit=gram_unit, ml_unit=ml_unit)


def downgrade() -> None:
    op.drop_constraint("uq_recipes_dish_sequence", "recipes", type_="unique")
    op.drop_constraint("uq_recipes_public_key", "recipes", type_="unique")
    op.drop_constraint("uq_dishes_public_key", "dishes", type_="unique")
    op.drop_column("recipes", "computed_traits_json")
    op.drop_column("recipes", "sequence_number")
    op.drop_column("recipes", "public_key")
    op.drop_column("dishes", "public_key")
    op.drop_column("ingredients", "food_group")
