"""Scope meal reviews by household and user.

Revision ID: 035_meal_reviews_household_user
Revises: 034_household_ownership
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "035_meal_reviews_household_user"
down_revision: Union[str, Sequence[str], None] = "034_household_ownership"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_HOUSEHOLD_ID = "00000000-0000-4000-8000-000000000001"


def upgrade() -> None:
    op.add_column("meal_ratings", sa.Column("household_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("meal_ratings", sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.execute(
        sa.text(
            """
            UPDATE meal_ratings mr
            SET household_id = mp.household_id
            FROM meal_plan_items mpi
            JOIN meal_plans mp ON mp.id = mpi.meal_plan_id
            WHERE mpi.id = mr.meal_plan_item_id
            """
        )
    )
    op.execute(
        sa.text("UPDATE meal_ratings SET household_id = CAST(:household_id AS uuid) WHERE household_id IS NULL")
        .bindparams(household_id=DEFAULT_HOUSEHOLD_ID)
    )
    op.alter_column("meal_ratings", "household_id", nullable=False)
    op.create_foreign_key(
        "fk_meal_ratings_household_id_households",
        "meal_ratings",
        "households",
        ["household_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_meal_ratings_user_id_users",
        "meal_ratings",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(op.f("ix_meal_ratings_household_id"), "meal_ratings", ["household_id"], unique=False)
    op.create_index(op.f("ix_meal_ratings_user_id"), "meal_ratings", ["user_id"], unique=False)
    op.drop_constraint("uq_meal_ratings_meal_plan_item", "meal_ratings", type_="unique")
    op.create_unique_constraint(
        "uq_meal_ratings_item_user",
        "meal_ratings",
        ["meal_plan_item_id", "user_id"],
    )
    op.rename_table("meal_ratings", "meal_reviews")


def downgrade() -> None:
    op.rename_table("meal_reviews", "meal_ratings")
    op.drop_constraint("uq_meal_ratings_item_user", "meal_ratings", type_="unique")
    op.create_unique_constraint("uq_meal_ratings_meal_plan_item", "meal_ratings", ["meal_plan_item_id"])
    op.drop_index(op.f("ix_meal_ratings_user_id"), table_name="meal_ratings")
    op.drop_index(op.f("ix_meal_ratings_household_id"), table_name="meal_ratings")
    op.drop_constraint("fk_meal_ratings_user_id_users", "meal_ratings", type_="foreignkey")
    op.drop_constraint("fk_meal_ratings_household_id_households", "meal_ratings", type_="foreignkey")
    op.drop_column("meal_ratings", "user_id")
    op.drop_column("meal_ratings", "household_id")
