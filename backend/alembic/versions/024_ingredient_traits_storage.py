"""Add ingredient traits_json and storage_after_opening."""

from alembic import op
import sqlalchemy as sa

revision = "024_ingredient_traits_storage"
down_revision = "023_ingredient_taxonomy_metadata"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ingredients", sa.Column("storage_after_opening", sa.String(length=32), nullable=True))
    op.add_column("ingredients", sa.Column("traits_json", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("ingredients", "traits_json")
    op.drop_column("ingredients", "storage_after_opening")
