"""Add per-meal source breakdown to shopping list items.

Revision ID: 016_shopping_contributions
Revises: 015_shopping_lists
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "016_shopping_contributions"
down_revision: Union[str, Sequence[str], None] = "015_shopping_lists"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    column_names = {column["name"] for column in inspector.get_columns("shopping_list_items")}
    if "source_contributions_json" in column_names:
        return

    op.add_column(
        "shopping_list_items",
        sa.Column(
            "source_contributions_json",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    column_names = {column["name"] for column in inspector.get_columns("shopping_list_items")}
    if "source_contributions_json" not in column_names:
        return

    op.drop_column("shopping_list_items", "source_contributions_json")
