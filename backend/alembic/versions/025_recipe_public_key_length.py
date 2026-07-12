"""Widen recipe public_key for four-digit sequence suffixes."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "025_recipe_public_key_length"
down_revision: Union[str, Sequence[str], None] = "024_ingredient_traits_storage"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "recipes",
        "public_key",
        existing_type=sa.String(length=36),
        type_=sa.String(length=40),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "recipes",
        "public_key",
        existing_type=sa.String(length=40),
        type_=sa.String(length=36),
        existing_nullable=False,
    )
