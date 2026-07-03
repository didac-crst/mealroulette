"""Add meal plans, plan items, and ratings.

Revision ID: 011_meal_planning
Revises: 010_dish_course_simplify
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "011_meal_planning"
down_revision: Union[str, Sequence[str], None] = "010_dish_course_simplify"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

meal_plan_status = postgresql.ENUM(
    "draft", "active", "archived", name="meal_plan_status", create_type=False
)
meal_slot = postgresql.ENUM("lunch", "dinner", name="meal_slot", create_type=False)
meal_plan_item_status = postgresql.ENUM(
    "planned",
    "cooked",
    "skipped",
    "leftovers",
    "cancelled",
    name="meal_plan_item_status",
    create_type=False,
)


def upgrade() -> None:
    meal_plan_status.create(op.get_bind(), checkfirst=True)
    meal_slot.create(op.get_bind(), checkfirst=True)
    meal_plan_item_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "meal_plans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("week_start_date", sa.Date(), nullable=False),
        sa.Column("status", meal_plan_status, nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("week_start_date", name="uq_meal_plans_week_start"),
    )
    op.create_index("ix_meal_plans_week_start_date", "meal_plans", ["week_start_date"])

    op.create_table(
        "meal_plan_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("meal_plan_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("meal_slot", meal_slot, nullable=False),
        sa.Column("dish_id", sa.Integer(), nullable=True),
        sa.Column("recipe_id", sa.Integer(), nullable=True),
        sa.Column("status", meal_plan_item_status, nullable=False, server_default="planned"),
        sa.Column("locked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("manually_selected", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("skip_reason", sa.String(length=255), nullable=True),
        sa.Column("leftover_source_item_id", sa.Integer(), nullable=True),
        sa.Column("selection_reasons_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["dish_id"], ["dishes.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["leftover_source_item_id"], ["meal_plan_items.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["meal_plan_id"], ["meal_plans.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recipe_id"], ["recipes.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("meal_plan_id", "date", "meal_slot", name="uq_meal_plan_items_slot"),
    )
    op.create_index("ix_meal_plan_items_meal_plan_id", "meal_plan_items", ["meal_plan_id"])
    op.create_index("ix_meal_plan_items_dish_id", "meal_plan_items", ["dish_id"])
    op.create_index("ix_meal_plan_items_recipe_id", "meal_plan_items", ["recipe_id"])
    op.create_index(
        "ix_meal_plan_items_leftover_source_item_id",
        "meal_plan_items",
        ["leftover_source_item_id"],
    )

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


def downgrade() -> None:
    op.drop_index("ix_ratings_user_id", table_name="ratings")
    op.drop_index("ix_ratings_dish_id", table_name="ratings")
    op.drop_table("ratings")
    op.drop_index("ix_meal_plan_items_leftover_source_item_id", table_name="meal_plan_items")
    op.drop_index("ix_meal_plan_items_recipe_id", table_name="meal_plan_items")
    op.drop_index("ix_meal_plan_items_dish_id", table_name="meal_plan_items")
    op.drop_index("ix_meal_plan_items_meal_plan_id", table_name="meal_plan_items")
    op.drop_table("meal_plan_items")
    op.drop_index("ix_meal_plans_week_start_date", table_name="meal_plans")
    op.drop_table("meal_plans")
    meal_plan_item_status.drop(op.get_bind(), checkfirst=True)
    meal_slot.drop(op.get_bind(), checkfirst=True)
    meal_plan_status.drop(op.get_bind(), checkfirst=True)
