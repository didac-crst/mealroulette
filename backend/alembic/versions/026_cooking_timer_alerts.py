"""Cooking timer Telegram alerts.

Revision ID: 026_cooking_timer_alerts
Revises: 025_recipe_public_key_length
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "026_cooking_timer_alerts"
down_revision: Union[str, Sequence[str], None] = "025_recipe_public_key_length"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cooking_timer_alerts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("recipe_id", sa.Integer(), nullable=False),
        sa.Column("recipe_step_id", sa.Integer(), nullable=False),
        sa.Column("step_number", sa.Integer(), nullable=False),
        sa.Column("dish_name", sa.String(length=255), nullable=False),
        sa.Column("recipe_name", sa.String(length=255), nullable=False),
        sa.Column("fire_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="pending"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recipe_id"], ["recipes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recipe_step_id"], ["recipe_steps.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("step_number >= 1", name="ck_cooking_timer_alerts_step_number"),
    )
    op.create_index(
        "ix_cooking_timer_alerts_pending_fire_at",
        "cooking_timer_alerts",
        ["fire_at"],
        postgresql_where=sa.text("status = 'pending'"),
    )


def downgrade() -> None:
    op.drop_index("ix_cooking_timer_alerts_pending_fire_at", table_name="cooking_timer_alerts")
    op.drop_table("cooking_timer_alerts")
