"""Telegram reminder settings and subscribers.

Revision ID: 019_telegram_settings
Revises: 018_ingredient_conversion_unique
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "019_telegram_settings"
down_revision: Union[str, Sequence[str], None] = "018_ingredient_conversion_unique"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "telegram_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("daily_reminder_time", sa.Time(), nullable=False, server_default=sa.text("'08:00:00'")),
        sa.Column("shopping_window_days", sa.Integer(), nullable=False, server_default=sa.text("3")),
        sa.Column("include_today", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("include_pantry_items", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("group_by_category", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="Europe/Paris"),
        sa.Column("last_update_id", sa.BigInteger(), nullable=True),
        sa.Column("last_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("shopping_window_days >= 1 AND shopping_window_days <= 14", name="ck_telegram_window_days"),
    )
    op.execute(sa.text("INSERT INTO telegram_settings (id, enabled) VALUES (1, false)"))

    op.create_table(
        "telegram_subscribers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chat_id", sa.String(length=64), nullable=False),
        sa.Column("telegram_user_id", sa.String(length=64), nullable=True),
        sa.Column("username", sa.String(length=64), nullable=True),
        sa.Column("display_name", sa.String(length=128), nullable=True),
        sa.Column("subscribed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chat_id", name="uq_telegram_subscribers_chat_id"),
    )


def downgrade() -> None:
    op.drop_table("telegram_subscribers")
    op.drop_table("telegram_settings")
