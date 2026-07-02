"""Reference data seeding moved to startup CLI (no-op for history).

Revision ID: 004_seed_units_tags
Revises: 003_catalog
Create Date: 2026-07-02 00:00:00.000000

Databases stamped with this revision applied seed data via Alembic before the
YAML-based `seed_reference_data` flow. New installs rely on the API entrypoint
instead; this revision remains so existing databases keep a valid Alembic chain.
"""

from typing import Sequence, Union

revision: str = "004_seed_units_tags"
down_revision: Union[str, Sequence[str], None] = "003_catalog"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
