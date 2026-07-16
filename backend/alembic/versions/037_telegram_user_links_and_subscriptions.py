"""Add Telegram user links and household notification subscriptions.

Revision ID: 037_telegram_user_links_and_subscriptions
Revises: 036_household_invitations
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "037_telegram_user_links_and_subscriptions"
down_revision: Union[str, Sequence[str], None] = "036_household_invitations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
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
    op.create_index("ix_telegram_link_tokens_user_id", "telegram_link_tokens", ["user_id"])

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
    )
    op.create_index("ix_telegram_user_links_user_id", "telegram_user_links", ["user_id"])
    op.create_index("ix_telegram_user_links_chat_id", "telegram_user_links", ["chat_id"])

    op.create_table(
        "household_notification_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("household_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("notify_daily_reminder", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notify_shopping", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notify_roulette", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("daily_reminder_time", sa.Time(), nullable=False, server_default="08:00:00"),
        sa.Column("shopping_window_days", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="Europe/Paris"),
        sa.Column("last_reminder_sent_at", sa.DateTime(timezone=True), nullable=True),
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
    op.create_index(
        "ix_household_notification_subscriptions_user_id",
        "household_notification_subscriptions",
        ["user_id"],
    )
    op.create_index(
        "ix_household_notification_subscriptions_household_id",
        "household_notification_subscriptions",
        ["household_id"],
    )

    # Ensure every household has telegram_settings (034 only backfilled the default).
    op.execute(
        """
        INSERT INTO telegram_settings (
            household_id, enabled, daily_reminder_time, shopping_window_days,
            include_today, include_pantry_items, group_by_category, timezone
        )
        SELECT
            h.id, false, TIME '08:00:00', 3, true, false, true, 'Europe/Paris'
        FROM households h
        WHERE NOT EXISTS (
            SELECT 1 FROM telegram_settings ts WHERE ts.household_id = h.id
        )
        """
    )

    # One subscription per active membership; schedule from household telegram_settings when present.
    op.execute(
        """
        INSERT INTO household_notification_subscriptions (
            id, user_id, household_id,
            notify_daily_reminder, notify_shopping, notify_roulette,
            daily_reminder_time, shopping_window_days, timezone
        )
        SELECT
            gen_random_uuid(),
            m.user_id,
            m.household_id,
            true,
            true,
            true,
            COALESCE(ts.daily_reminder_time, TIME '08:00:00'),
            COALESCE(ts.shopping_window_days, 3),
            COALESCE(ts.timezone, 'Europe/Paris')
        FROM household_memberships m
        LEFT JOIN telegram_settings ts ON ts.household_id = m.household_id
        WHERE m.active IS TRUE
          AND NOT EXISTS (
            SELECT 1
            FROM household_notification_subscriptions sub
            WHERE sub.user_id = m.user_id AND sub.household_id = m.household_id
          )
        """
    )


def downgrade() -> None:
    op.drop_table("household_notification_subscriptions")
    op.drop_table("telegram_user_links")
    op.drop_table("telegram_link_tokens")
