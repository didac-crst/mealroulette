"""Add difficulty to recipes.

Revision ID: 005_recipe_difficulty
Revises: 004_seed_units_tags
Create Date: 2026-07-02 18:20:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005_recipe_difficulty"
down_revision: Union[str, Sequence[str], None] = "004_seed_units_tags"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("recipes", sa.Column("difficulty", sa.String(length=32), nullable=True))


def downgrade() -> None:
    op.drop_column("recipes", "difficulty")
