"""Unique triplet constraint on ingredient unit conversions.

Revision ID: 018_ingredient_conversion_unique
Revises: 017_ingredient_unit_behavior
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "018_ingredient_conversion_unique"
down_revision: Union[str, Sequence[str], None] = "017_ingredient_unit_behavior"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_ingredient_unit_conversions_triplet",
        "ingredient_unit_conversions",
        ["ingredient_id", "from_unit_id", "to_unit_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_ingredient_unit_conversions_triplet",
        "ingredient_unit_conversions",
        type_="unique",
    )
