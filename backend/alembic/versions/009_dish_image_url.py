"""dish image_url

Revision ID: 009_dish_image_url
Revises: 008_recipe_is_main
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "009_dish_image_url"
down_revision: Union[str, Sequence[str], None] = "008_recipe_is_main"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("dishes", sa.Column("image_url", sa.String(length=512), nullable=True))


def downgrade() -> None:
    op.drop_column("dishes", "image_url")
