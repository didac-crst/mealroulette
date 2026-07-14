"""Composable meal dish lines and planning state.

Revision ID: 031_composable_meal_lines
Revises: 030_taxonomy_family_backfill
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "031_composable_meal_lines"
down_revision: Union[str, Sequence[str], None] = "030_taxonomy_family_backfill"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

meal_planning_state = postgresql.ENUM("open", "do_not_plan", name="meal_planning_state", create_type=False)
meal_plan_dish_line_role = postgresql.ENUM(
    "main",
    "centerpiece",
    "side",
    "dessert",
    "extra",
    name="meal_plan_dish_line_role",
    create_type=False,
)
meal_plan_dish_line_source = postgresql.ENUM(
    "roulette",
    "manual",
    "leftover",
    name="meal_plan_dish_line_source",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    postgresql.ENUM("open", "do_not_plan", name="meal_planning_state").create(bind, checkfirst=True)
    postgresql.ENUM(
        "main",
        "centerpiece",
        "side",
        "dessert",
        "extra",
        name="meal_plan_dish_line_role",
    ).create(bind, checkfirst=True)
    postgresql.ENUM("roulette", "manual", "leftover", name="meal_plan_dish_line_source").create(
        bind, checkfirst=True
    )

    op.add_column(
        "meal_plan_items",
        sa.Column(
            "planning_state",
            meal_planning_state,
            nullable=False,
            server_default="open",
        ),
    )

    op.create_table(
        "meal_plan_item_dishes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "meal_plan_item_id",
            sa.Integer(),
            sa.ForeignKey("meal_plan_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("dish_id", sa.Integer(), sa.ForeignKey("dishes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("recipe_id", sa.Integer(), sa.ForeignKey("recipes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("role", meal_plan_dish_line_role, nullable=False),
        sa.Column("source", meal_plan_dish_line_source, nullable=False),
        sa.Column("selection_reasons_json", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("meal_plan_item_id", "position", name="uq_meal_plan_item_dishes_position"),
        sa.CheckConstraint("position >= 0", name="ck_meal_plan_item_dishes_position_nonneg"),
    )
    op.create_index(
        "ix_meal_plan_item_dishes_meal_plan_item_id",
        "meal_plan_item_dishes",
        ["meal_plan_item_id"],
    )

    op.execute(
        sa.text(
            """
            INSERT INTO meal_plan_item_dishes (
                meal_plan_item_id,
                dish_id,
                recipe_id,
                position,
                role,
                source,
                selection_reasons_json,
                created_at,
                updated_at
            )
            SELECT
                mpi.id,
                mpi.dish_id,
                mpi.recipe_id,
                0,
                CASE
                    WHEN d.meal_composition = 'dessert' THEN 'dessert'
                    WHEN d.meal_composition = 'simple_dish' AND d.simple_dish_part = 'centerpiece' THEN 'centerpiece'
                    WHEN d.meal_composition = 'simple_dish' AND d.simple_dish_part = 'sidedish' THEN 'side'
                    ELSE 'main'
                END::meal_plan_dish_line_role,
                CASE
                    WHEN mpi.manually_selected THEN 'manual'
                    ELSE 'roulette'
                END::meal_plan_dish_line_source,
                mpi.selection_reasons_json,
                mpi.created_at,
                mpi.updated_at
            FROM meal_plan_items mpi
            JOIN dishes d ON d.id = mpi.dish_id
            WHERE mpi.dish_id IS NOT NULL
            """
        )
    )


def downgrade() -> None:
    op.drop_index("ix_meal_plan_item_dishes_meal_plan_item_id", table_name="meal_plan_item_dishes")
    op.drop_table("meal_plan_item_dishes")
    op.drop_column("meal_plan_items", "planning_state")
    postgresql.ENUM("roulette", "manual", "leftover", name="meal_plan_dish_line_source").drop(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM(
        "main",
        "centerpiece",
        "side",
        "dessert",
        "extra",
        name="meal_plan_dish_line_role",
    ).drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM("open", "do_not_plan", name="meal_planning_state").drop(op.get_bind(), checkfirst=True)
