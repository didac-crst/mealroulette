"""Remove unused migration placeholder household on greenfield installs.

Revision ID: 036_greenfield_household
Revises: 035_household_auth_extras
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "036_greenfield_household"
down_revision: Union[str, Sequence[str], None] = "035_household_auth_extras"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_HOUSEHOLD_ID = "00000000-0000-4000-8000-000000000001"

HOUSEHOLD_OWNED_TABLES = (
    "dishes",
    "meal_plans",
    "planning_rules",
    "shopping_lists",
    "scheduler_settings",
    "telegram_settings",
)


def upgrade() -> None:
    conditions = " AND ".join(
        f"NOT EXISTS (SELECT 1 FROM {table} t WHERE t.household_id = h.id)"
        for table in HOUSEHOLD_OWNED_TABLES
    )
    op.execute(
        f"""
        DELETE FROM households h
        WHERE h.id = CAST('{DEFAULT_HOUSEHOLD_ID}' AS uuid)
          AND NOT EXISTS (SELECT 1 FROM household_memberships m WHERE m.household_id = h.id)
          AND {conditions}
        """
    )


def downgrade() -> None:
    op.execute(
        f"""
        INSERT INTO households (id, name)
        SELECT CAST('{DEFAULT_HOUSEHOLD_ID}' AS uuid), 'Default household'
        WHERE NOT EXISTS (
            SELECT 1 FROM households WHERE id = CAST('{DEFAULT_HOUSEHOLD_ID}' AS uuid)
        )
        """
    )
