"""Computed traits, public keys, and ingredient food groups.

Revision ID: 022_computed_traits
Revises: 021_meal_plan_roulette_undo
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

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


def _backfill(session: Session) -> None:
    from mealroulette.services.food_groups import food_group_for_ingredient
    from mealroulette.services.public_keys import generate_dish_public_key, generate_recipe_public_key

    ingredients = sa.table(
        "ingredients",
        sa.column("id", sa.Integer),
        sa.column("category", sa.String),
        sa.column("food_group", sa.String),
    )
    dishes_table = sa.table(
        "dishes",
        sa.column("id", sa.Integer),
        sa.column("name", sa.String),
        sa.column("public_key", sa.String),
    )
    recipes_table = sa.table(
        "recipes",
        sa.column("id", sa.Integer),
        sa.column("dish_id", sa.Integer),
        sa.column("is_main", sa.Boolean),
        sa.column("public_key", sa.String),
        sa.column("sequence_number", sa.Integer),
        sa.column("computed_traits_json", JSONB),
    )

    for row in session.execute(sa.select(ingredients.c.id, ingredients.c.category, ingredients.c.food_group)):
        session.execute(
            ingredients.update()
            .where(ingredients.c.id == row.id)
            .values(
                food_group=food_group_for_ingredient(
                    food_group=row.food_group,
                    category=row.category,
                )
            )
        )

    existing_keys: set[str] = set()
    dishes = session.execute(sa.select(dishes_table.c.id, dishes_table.c.name).order_by(dishes_table.c.id)).all()
    for dish in dishes:
        for _ in range(20):
            candidate = generate_dish_public_key(dish.name)
            if candidate not in existing_keys:
                session.execute(
                    dishes_table.update()
                    .where(dishes_table.c.id == dish.id)
                    .values(public_key=candidate)
                )
                existing_keys.add(candidate)
                break
        else:
            raise RuntimeError(f"Could not generate unique public key for dish {dish.id}")

    if not dishes:
        return

    for dish in dishes:
        recipes = session.execute(
            sa.select(recipes_table.c.id, recipes_table.c.is_main)
            .where(recipes_table.c.dish_id == dish.id)
            .order_by(recipes_table.c.id)
        ).all()
        dish_public_key = session.scalar(
            sa.select(dishes_table.c.public_key).where(dishes_table.c.id == dish.id)
        )
        mains = [recipe for recipe in recipes if recipe.is_main]
        main_recipe = min(mains, key=lambda recipe: recipe.id) if mains else None
        rest = sorted(
            [recipe for recipe in recipes if main_recipe is None or recipe.id != main_recipe.id],
            key=lambda recipe: recipe.id,
        )
        ordered = ([main_recipe] if main_recipe is not None else []) + rest
        for sequence, recipe in enumerate(ordered, start=1):
            session.execute(
                recipes_table.update()
                .where(recipes_table.c.id == recipe.id)
                .values(
                    sequence_number=sequence,
                    public_key=generate_recipe_public_key(dish_public_key, sequence),
                    computed_traits_json=None,
                )
            )


def downgrade() -> None:
    op.drop_constraint("uq_recipes_dish_sequence", "recipes", type_="unique")
    op.drop_constraint("uq_recipes_public_key", "recipes", type_="unique")
    op.drop_constraint("uq_dishes_public_key", "dishes", type_="unique")
    op.drop_column("recipes", "computed_traits_json")
    op.drop_column("recipes", "sequence_number")
    op.drop_column("recipes", "public_key")
    op.drop_column("dishes", "public_key")
    op.drop_column("ingredients", "food_group")
