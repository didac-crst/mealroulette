"""Phase 15 slices 3-5: proposals, invitations, ratings split, Telegram links.

Revision ID: 035_household_auth_extras
Revises: 034_household_ownership
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "035_household_auth_extras"
down_revision: Union[str, Sequence[str], None] = "034_household_ownership"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_HOUSEHOLD_ID = "00000000-0000-4000-8000-000000000001"

proposal_status = postgresql.ENUM(
    "pending",
    "approved",
    "rejected",
    name="ingredient_proposal_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    proposal_status.create(bind, checkfirst=True)

    op.create_table(
        "ingredient_proposals",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("household_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("proposed_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("proposed_name", sa.String(length=128), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("status", proposal_status, nullable=False, server_default="pending"),
        sa.Column("reviewed_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["household_id"], ["households.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["proposed_by_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ingredient_proposals_household_id", "ingredient_proposals", ["household_id"])

    op.create_table(
        "household_invitations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("household_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accepted_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["household_id"], ["households.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["accepted_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash", name="uq_household_invitations_token_hash"),
    )
    op.create_index("ix_household_invitations_household_id", "household_invitations", ["household_id"])

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
        sa.text(
            "UPDATE meal_ratings SET household_id = CAST(:hid AS uuid) WHERE household_id IS NULL"
        ).bindparams(
            hid=DEFAULT_HOUSEHOLD_ID
        )
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
    op.drop_constraint("uq_meal_ratings_meal_plan_item", "meal_ratings", type_="unique")
    op.create_unique_constraint(
        "uq_meal_ratings_item_user",
        "meal_ratings",
        ["meal_plan_item_id", "user_id"],
    )
    op.rename_table("meal_ratings", "meal_reviews")

    op.create_table(
        "recipe_ratings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("household_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dish_id", sa.Integer(), nullable=False),
        sa.Column("recipe_id", sa.Integer(), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["household_id"], ["households.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["dish_id"], ["dishes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recipe_id"], ["recipes.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "household_id",
            "user_id",
            "dish_id",
            "recipe_id",
            name="uq_recipe_ratings_household_user_dish_recipe",
        ),
    )

    op.create_table(
        "telegram_link_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash", name="uq_telegram_link_tokens_token_hash"),
    )

    op.create_table(
        "telegram_user_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chat_id", sa.String(length=64), nullable=False),
        sa.Column("telegram_user_id", sa.String(length=64), nullable=True),
        sa.Column("username", sa.String(length=64), nullable=True),
        sa.Column("display_name", sa.String(length=128), nullable=True),
        sa.Column("linked_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_telegram_user_links_user_id"),
        sa.UniqueConstraint("chat_id", name="uq_telegram_user_links_chat_id"),
    )

    op.create_table(
        "household_notification_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("household_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("notify_daily_reminder", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notify_shopping", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notify_roulette", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["household_id"], ["households.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "household_id",
            name="uq_household_notification_subscriptions_user_household",
        ),
    )


def downgrade() -> None:
    op.drop_table("household_notification_subscriptions")
    op.drop_table("telegram_user_links")
    op.drop_table("telegram_link_tokens")
    op.drop_table("recipe_ratings")

    op.rename_table("meal_reviews", "meal_ratings")
    op.drop_constraint("uq_meal_ratings_item_user", "meal_ratings", type_="unique")
    op.create_unique_constraint("uq_meal_ratings_meal_plan_item", "meal_ratings", ["meal_plan_item_id"])
    op.drop_constraint("fk_meal_ratings_user_id_users", "meal_ratings", type_="foreignkey")
    op.drop_constraint("fk_meal_ratings_household_id_households", "meal_ratings", type_="foreignkey")
    op.drop_column("meal_ratings", "user_id")
    op.drop_column("meal_ratings", "household_id")

    op.drop_index("ix_household_invitations_household_id", table_name="household_invitations")
    op.drop_table("household_invitations")
    op.drop_index("ix_ingredient_proposals_household_id", table_name="ingredient_proposals")
    op.drop_table("ingredient_proposals")
    proposal_status.drop(op.get_bind(), checkfirst=True)
