"""Add household_id to household-owned root aggregates.

Revision ID: 034_household_ownership
Revises: 033_household_tenancy_identity
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "034_household_ownership"
down_revision: Union[str, Sequence[str], None] = "033_household_tenancy_identity"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_HOUSEHOLD_ID = "00000000-0000-4000-8000-000000000001"


def _add_household_id(table: str) -> None:
    op.add_column(
        table,
        sa.Column("household_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.execute(
        sa.text(f"UPDATE {table} SET household_id = CAST(:household_id AS uuid)").bindparams(
            household_id=DEFAULT_HOUSEHOLD_ID
        )
    )
    op.alter_column(table, "household_id", nullable=False)
    op.create_foreign_key(
        f"fk_{table}_household_id_households",
        table,
        "households",
        ["household_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(op.f(f"ix_{table}_household_id"), table, ["household_id"], unique=False)


def upgrade() -> None:
    _add_household_id("dishes")
    op.drop_index(op.f("ix_dishes_name"), table_name="dishes")
    # Dish names are household-scoped; public keys remain globally unique because recipe
    # public keys are derived from dish public keys and recipes keep a global unique index.
    op.create_unique_constraint("uq_dishes_household_name", "dishes", ["household_id", "name"])

    _add_household_id("meal_plans")
    op.drop_constraint("uq_meal_plans_week_start", "meal_plans", type_="unique")
    op.create_unique_constraint(
        "uq_meal_plans_household_week",
        "meal_plans",
        ["household_id", "week_start_date"],
    )

    _add_household_id("planning_rules")
    op.drop_constraint("uq_planning_rules_name", "planning_rules", type_="unique")
    op.create_unique_constraint(
        "uq_planning_rules_household_name",
        "planning_rules",
        ["household_id", "name"],
    )

    _add_household_id("shopping_lists")

    _add_household_id("scheduler_settings")
    op.create_unique_constraint(
        "uq_scheduler_settings_household_id",
        "scheduler_settings",
        ["household_id"],
    )

    _add_household_id("telegram_settings")
    op.create_unique_constraint(
        "uq_telegram_settings_household_id",
        "telegram_settings",
        ["household_id"],
    )


def downgrade() -> None:
    raise NotImplementedError(
        "Downgrade is not supported for household ownership migration; "
        "dropping household_id and restoring global uniqueness is not data-safe."
    )
