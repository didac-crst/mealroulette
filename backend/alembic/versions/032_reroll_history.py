"""Add reroll history to meal plan items.

Revision ID: 032_reroll_history
Revises: 031_composable_meal_lines
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "032_reroll_history"
down_revision = "031_composable_meal_lines"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("meal_plan_items", sa.Column("reroll_history_json", JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("meal_plan_items", "reroll_history_json")
