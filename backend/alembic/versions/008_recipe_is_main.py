"""recipe is_main flag

Revision ID: 008_recipe_is_main
Revises: 007_dish_recipe_ownership
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "008_recipe_is_main"
down_revision: Union[str, Sequence[str], None] = "007_dish_recipe_ownership"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("recipes", sa.Column("is_main", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.execute(
        """
        UPDATE recipes AS r
        SET is_main = TRUE
        FROM (
            SELECT DISTINCT ON (dish_id) id
            FROM recipes
            ORDER BY dish_id, id ASC
        ) AS first_recipe
        WHERE r.id = first_recipe.id
        """
    )
    op.alter_column("recipes", "is_main", server_default=None)


def downgrade() -> None:
    op.drop_column("recipes", "is_main")
