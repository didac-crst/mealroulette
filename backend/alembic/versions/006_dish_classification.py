"""Add structured dish classification fields.

Revision ID: 006_dish_classification
Revises: 005_recipe_difficulty
Create Date: 2026-07-02 19:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006_dish_classification"
down_revision: Union[str, Sequence[str], None] = "005_recipe_difficulty"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

dish_course = sa.Enum(
    "main",
    "side",
    "starter",
    "dessert",
    "snack",
    "sauce_condiment",
    name="dish_course",
)
dish_status = sa.Enum("draft", "active", "archived", name="dish_status")
vegetable_level = sa.Enum("low", "medium", "high", "vegetable_main", name="vegetable_level")


def upgrade() -> None:
    dish_course.create(op.get_bind(), checkfirst=True)
    dish_status.create(op.get_bind(), checkfirst=True)
    vegetable_level.create(op.get_bind(), checkfirst=True)

    op.add_column("dishes", sa.Column("course", dish_course, nullable=True))
    op.add_column(
        "dishes",
        sa.Column("status", dish_status, nullable=False, server_default="active"),
    )
    op.add_column("dishes", sa.Column("vegetable_level", vegetable_level, nullable=True))
    op.add_column("dishes", sa.Column("dominant_protein", sa.String(length=64), nullable=True))
    op.add_column("dishes", sa.Column("dominant_carb", sa.String(length=64), nullable=True))
    op.add_column("dishes", sa.Column("suitable_for_lunch", sa.Boolean(), nullable=True))
    op.add_column("dishes", sa.Column("suitable_for_dinner", sa.Boolean(), nullable=True))
    op.add_column("dishes", sa.Column("weekday_friendly", sa.Boolean(), nullable=True))
    op.add_column("dishes", sa.Column("leftovers_possible", sa.Boolean(), nullable=True))
    op.add_column("dishes", sa.Column("freezer_friendly", sa.Boolean(), nullable=True))

    op.execute("UPDATE dishes SET status = 'archived' WHERE active IS FALSE")
    op.execute("UPDATE dishes SET status = 'active' WHERE active IS TRUE")


def downgrade() -> None:
    op.drop_column("dishes", "freezer_friendly")
    op.drop_column("dishes", "leftovers_possible")
    op.drop_column("dishes", "weekday_friendly")
    op.drop_column("dishes", "suitable_for_dinner")
    op.drop_column("dishes", "suitable_for_lunch")
    op.drop_column("dishes", "dominant_carb")
    op.drop_column("dishes", "dominant_protein")
    op.drop_column("dishes", "vegetable_level")
    op.drop_column("dishes", "status")
    op.drop_column("dishes", "course")

    vegetable_level.drop(op.get_bind(), checkfirst=True)
    dish_status.drop(op.get_bind(), checkfirst=True)
    dish_course.drop(op.get_bind(), checkfirst=True)
