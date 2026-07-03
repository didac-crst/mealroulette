"""Rename meal statuses and plan item fields for eaten/ate_leftovers model.

Revision ID: 012_meal_item_eaten_status
Revises: 011_meal_planning
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "012_meal_item_eaten_status"
down_revision: Union[str, Sequence[str], None] = "011_meal_planning"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("meal_plan_items", "locked", new_column_name="is_locked")
    op.add_column("meal_plan_items", sa.Column("skip_comment", sa.Text(), nullable=True))

    op.execute("ALTER TABLE meal_plan_items ALTER COLUMN status DROP DEFAULT")
    op.execute("ALTER TYPE meal_plan_item_status RENAME TO meal_plan_item_status_old")
    op.execute(
        """
        CREATE TYPE meal_plan_item_status AS ENUM (
            'planned', 'eaten', 'skipped', 'ate_leftovers'
        )
        """
    )
    op.execute(
        """
        ALTER TABLE meal_plan_items
        ALTER COLUMN status TYPE meal_plan_item_status
        USING (
            CASE status::text
                WHEN 'cooked' THEN 'eaten'
                WHEN 'leftovers' THEN 'ate_leftovers'
                WHEN 'cancelled' THEN 'skipped'
                ELSE status::text
            END
        )::meal_plan_item_status
        """
    )
    op.execute("ALTER TABLE meal_plan_items ALTER COLUMN status SET DEFAULT 'planned'::meal_plan_item_status")
    op.execute("DROP TYPE meal_plan_item_status_old")


def downgrade() -> None:
    op.execute("ALTER TABLE meal_plan_items ALTER COLUMN status DROP DEFAULT")
    op.execute("ALTER TYPE meal_plan_item_status RENAME TO meal_plan_item_status_new")
    op.execute(
        """
        CREATE TYPE meal_plan_item_status AS ENUM (
            'planned', 'cooked', 'skipped', 'leftovers', 'cancelled'
        )
        """
    )
    op.execute(
        """
        ALTER TABLE meal_plan_items
        ALTER COLUMN status TYPE meal_plan_item_status
        USING (
            CASE status::text
                WHEN 'eaten' THEN 'cooked'
                WHEN 'ate_leftovers' THEN 'leftovers'
                ELSE status::text
            END
        )::meal_plan_item_status
        """
    )
    op.execute("ALTER TABLE meal_plan_items ALTER COLUMN status SET DEFAULT 'planned'::meal_plan_item_status")
    op.execute("DROP TYPE meal_plan_item_status_new")

    op.drop_column("meal_plan_items", "skip_comment")
    op.alter_column("meal_plan_items", "is_locked", new_column_name="locked")
