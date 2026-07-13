"""Promote YAML taxonomy to first-class database tables.

Revision ID: 028_taxonomy_tables
Revises: 027_dish_meal_composition
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "028_taxonomy_tables"
down_revision: Union[str, Sequence[str], None] = "027_dish_meal_composition"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "food_groups",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("label", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "ingredient_families",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column(
            "food_group_id",
            sa.String(length=64),
            sa.ForeignKey("food_groups.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("label", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ingredient_families_food_group_id", "ingredient_families", ["food_group_id"])

    op.add_column(
        "ingredients",
        sa.Column(
            "family_id",
            sa.String(length=64),
            sa.ForeignKey("ingredient_families.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_ingredients_family_id", "ingredients", ["family_id"])

    from sqlalchemy.orm import Session

    from mealroulette.data.seed_taxonomy import seed_taxonomy_data

    bind = op.get_bind()
    with Session(bind) as db:
        seed_taxonomy_data(db, commit=False)


def downgrade() -> None:
    op.drop_index("ix_ingredients_family_id", table_name="ingredients")
    op.drop_column("ingredients", "family_id")
    op.drop_index("ix_ingredient_families_food_group_id", table_name="ingredient_families")
    op.drop_table("ingredient_families")
    op.drop_table("food_groups")
