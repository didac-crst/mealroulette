"""Rename planned_dish_id to dish_id and replace ratings with meal_ratings.

Revision ID: 013_meal_ratings_dish_id
Revises: 012_meal_item_eaten_status
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "013_meal_ratings_dish_id"
down_revision: Union[str, Sequence[str], None] = "012_meal_item_eaten_status"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("meal_plan_items", "planned_dish_id", new_column_name="dish_id")

    op.drop_index("ix_ratings_user_id", table_name="ratings")
    op.drop_index("ix_ratings_dish_id", table_name="ratings")
    op.drop_table("ratings")

    op.create_table(
        "meal_ratings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("meal_plan_item_id", sa.Integer(), nullable=False),
        sa.Column("dish_id", sa.Integer(), nullable=False),
        sa.Column("recipe_id", sa.Integer(), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["dish_id"], ["dishes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["meal_plan_item_id"], ["meal_plan_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recipe_id"], ["recipes.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("meal_plan_item_id", name="uq_meal_ratings_meal_plan_item"),
    )
    op.create_index("ix_meal_ratings_dish_id", "meal_ratings", ["dish_id"])
    op.create_index("ix_meal_ratings_meal_plan_item_id", "meal_ratings", ["meal_plan_item_id"])


def downgrade() -> None:
    op.drop_index("ix_meal_ratings_meal_plan_item_id", table_name="meal_ratings")
    op.drop_index("ix_meal_ratings_dish_id", table_name="meal_ratings")
    op.drop_table("meal_ratings")

    op.create_table(
        "ratings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("dish_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["dish_id"], ["dishes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dish_id", "user_id", name="uq_ratings_dish_user"),
    )
    op.create_index("ix_ratings_dish_id", "ratings", ["dish_id"])
    op.create_index("ix_ratings_user_id", "ratings", ["user_id"])

    op.alter_column("meal_plan_items", "dish_id", new_column_name="planned_dish_id")
