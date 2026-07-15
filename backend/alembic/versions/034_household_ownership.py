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
    op.drop_constraint("uq_dishes_public_key", "dishes", type_="unique")
    op.create_unique_constraint("uq_dishes_household_name", "dishes", ["household_id", "name"])
    op.create_unique_constraint("uq_dishes_household_public_key", "dishes", ["household_id", "public_key"])

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
    op.drop_constraint("uq_telegram_settings_household_id", "telegram_settings", type_="unique")
    op.drop_index(op.f("ix_telegram_settings_household_id"), table_name="telegram_settings")
    op.drop_constraint("fk_telegram_settings_household_id_households", "telegram_settings", type_="foreignkey")
    op.drop_column("telegram_settings", "household_id")

    op.drop_constraint("uq_scheduler_settings_household_id", "scheduler_settings", type_="unique")
    op.drop_index(op.f("ix_scheduler_settings_household_id"), table_name="scheduler_settings")
    op.drop_constraint("fk_scheduler_settings_household_id_households", "scheduler_settings", type_="foreignkey")
    op.drop_column("scheduler_settings", "household_id")

    op.drop_index(op.f("ix_shopping_lists_household_id"), table_name="shopping_lists")
    op.drop_constraint("fk_shopping_lists_household_id_households", "shopping_lists", type_="foreignkey")
    op.drop_column("shopping_lists", "household_id")

    op.drop_constraint("uq_planning_rules_household_name", "planning_rules", type_="unique")
    op.drop_index(op.f("ix_planning_rules_household_id"), table_name="planning_rules")
    op.drop_constraint("fk_planning_rules_household_id_households", "planning_rules", type_="foreignkey")
    op.drop_column("planning_rules", "household_id")
    op.create_unique_constraint("uq_planning_rules_name", "planning_rules", ["name"])

    op.drop_constraint("uq_meal_plans_household_week", "meal_plans", type_="unique")
    op.drop_index(op.f("ix_meal_plans_household_id"), table_name="meal_plans")
    op.drop_constraint("fk_meal_plans_household_id_households", "meal_plans", type_="foreignkey")
    op.drop_column("meal_plans", "household_id")
    op.create_unique_constraint("uq_meal_plans_week_start", "meal_plans", ["week_start_date"])

    op.drop_constraint("uq_dishes_household_public_key", "dishes", type_="unique")
    op.drop_constraint("uq_dishes_household_name", "dishes", type_="unique")
    op.drop_index(op.f("ix_dishes_household_id"), table_name="dishes")
    op.drop_constraint("fk_dishes_household_id_households", "dishes", type_="foreignkey")
    op.drop_column("dishes", "household_id")
    op.create_unique_constraint("uq_dishes_public_key", "dishes", ["public_key"])
    op.create_index(op.f("ix_dishes_name"), "dishes", ["name"], unique=True)
