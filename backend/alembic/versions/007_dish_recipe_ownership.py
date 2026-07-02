"""Clarify dish defaults vs recipe overrides and planning fields.

Revision ID: 007_dish_recipe_ownership
Revises: 006_dish_classification
Create Date: 2026-07-02 20:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "007_dish_recipe_ownership"
down_revision: Union[str, Sequence[str], None] = "006_dish_classification"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

serving_temperature = sa.Enum("hot", "cold", "room", "either", name="serving_temperature")
recipe_type = sa.Enum("standard", "thermomix", "other_appliance", name="recipe_type")


def upgrade() -> None:
    op.alter_column("dishes", "prep_time_minutes", new_column_name="default_prep_time_minutes")
    op.alter_column("dishes", "cook_time_minutes", new_column_name="default_cook_time_minutes")
    op.alter_column("dishes", "difficulty", new_column_name="default_difficulty")

    serving_temperature.create(op.get_bind(), checkfirst=True)
    recipe_type.create(op.get_bind(), checkfirst=True)

    op.add_column("dishes", sa.Column("kids_friendly", sa.Boolean(), nullable=True))
    op.add_column("dishes", sa.Column("serving_temperature", serving_temperature, nullable=True))
    op.add_column("dishes", sa.Column("thermomix_possible", sa.Boolean(), nullable=True))

    op.add_column(
        "recipes",
        sa.Column("recipe_type", recipe_type, nullable=False, server_default="standard"),
    )
    op.add_column("recipes", sa.Column("thermomix_model", sa.String(length=32), nullable=True))
    op.execute("UPDATE recipes SET recipe_type = 'thermomix' WHERE is_thermomix IS TRUE")


def downgrade() -> None:
    op.drop_column("recipes", "thermomix_model")
    op.drop_column("recipes", "recipe_type")

    op.drop_column("dishes", "thermomix_possible")
    op.drop_column("dishes", "serving_temperature")
    op.drop_column("dishes", "kids_friendly")

    op.alter_column("dishes", "default_difficulty", new_column_name="difficulty")
    op.alter_column("dishes", "default_cook_time_minutes", new_column_name="cook_time_minutes")
    op.alter_column("dishes", "default_prep_time_minutes", new_column_name="prep_time_minutes")

    recipe_type.drop(op.get_bind(), checkfirst=True)
    serving_temperature.drop(op.get_bind(), checkfirst=True)
