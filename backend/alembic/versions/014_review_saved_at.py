"""Add review_saved_at to meal plan items.

Revision ID: 014_review_saved_at
Revises: 013_meal_ratings_dish_id
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "014_review_saved_at"
down_revision: Union[str, Sequence[str], None] = "013_meal_ratings_dish_id"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "meal_plan_items",
        sa.Column("review_saved_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("meal_plan_items", "review_saved_at")
