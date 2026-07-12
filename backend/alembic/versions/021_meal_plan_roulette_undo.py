"""Add undo snapshot storage for meal-plan roulette actions.

Revision ID: 021_meal_plan_roulette_undo
Revises: 020_scheduler_planning_rules
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "021_meal_plan_roulette_undo"
down_revision: Union[str, Sequence[str], None] = "020_scheduler_planning_rules"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("meal_plans", sa.Column("last_roulette_undo_json", JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("meal_plans", "last_roulette_undo_json")
