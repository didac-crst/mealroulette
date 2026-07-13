"""Dish meal composition for planner slots.

Revision ID: 027_dish_meal_composition
Revises: 026_cooking_timer_alerts
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "027_dish_meal_composition"
down_revision: Union[str, Sequence[str], None] = "026_cooking_timer_alerts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

meal_composition = sa.Enum(
    "main_dish",
    "simple_dish",
    "dessert",
    name="meal_composition",
)
simple_dish_part = sa.Enum(
    "centerpiece",
    "sidedish",
    name="simple_dish_part",
)


def upgrade() -> None:
    bind = op.get_bind()
    meal_composition.create(bind, checkfirst=True)
    simple_dish_part.create(bind, checkfirst=True)

    op.add_column(
        "dishes",
        sa.Column(
            "meal_composition",
            meal_composition,
            nullable=False,
            server_default="main_dish",
        ),
    )
    op.add_column(
        "dishes",
        sa.Column("simple_dish_part", simple_dish_part, nullable=True),
    )

    op.execute("UPDATE dishes SET meal_composition = 'dessert' WHERE course = 'dessert'")

    op.create_check_constraint(
        "ck_dishes_simple_dish_part",
        "dishes",
        "(meal_composition = 'simple_dish' AND simple_dish_part IS NOT NULL) "
        "OR (meal_composition != 'simple_dish' AND simple_dish_part IS NULL)",
    )


def downgrade() -> None:
    op.drop_constraint("ck_dishes_simple_dish_part", "dishes", type_="check")
    op.drop_column("dishes", "simple_dish_part")
    op.drop_column("dishes", "meal_composition")
    simple_dish_part.drop(op.get_bind(), checkfirst=True)
    meal_composition.drop(op.get_bind(), checkfirst=True)
