"""Add ingredient taxonomy metadata columns."""

from alembic import op
import sqlalchemy as sa

revision = "023_ingredient_taxonomy_metadata"
down_revision = "022_computed_traits"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ingredients", sa.Column("storage_class", sa.String(length=32), nullable=True))
    op.add_column("ingredients", sa.Column("culinary_category", sa.String(length=64), nullable=True))
    op.add_column("ingredients", sa.Column("product_form", sa.String(length=32), nullable=True))
    op.add_column("ingredients", sa.Column("preservation", sa.String(length=32), nullable=True))


def downgrade() -> None:
    op.drop_column("ingredients", "preservation")
    op.drop_column("ingredients", "product_form")
    op.drop_column("ingredients", "culinary_category")
    op.drop_column("ingredients", "storage_class")
