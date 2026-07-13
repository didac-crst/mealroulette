"""Backfill ingredient family_id from seed YAML and legacy aliases.

Revision ID: 030_taxonomy_family_backfill
Revises: 029_backup_tables
"""

from typing import Sequence, Union

from alembic import op

revision: str = "030_taxonomy_family_backfill"
down_revision: Union[str, Sequence[str], None] = "029_backup_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from sqlalchemy.orm import Session

    from mealroulette.data.seed_taxonomy import seed_taxonomy_data

    bind = op.get_bind()
    with Session(bind) as db:
        seed_taxonomy_data(db, commit=False)


def downgrade() -> None:
    pass
