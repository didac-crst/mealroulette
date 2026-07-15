"""User-level Telegram reminder schedule on notification subscriptions.

Revision ID: 039_user_tg_reminder_sched
Revises: 038_telegram_login_otp
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "039_user_tg_reminder_sched"
down_revision: Union[str, Sequence[str], None] = "038_telegram_login_otp"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    columns = {col["name"] for col in inspect(bind).get_columns(table)}
    return column in columns


def upgrade() -> None:
    # Idempotent: a previous attempt with an over-long revision id may have
    # added these columns before failing to write alembic_version.
    if not _has_column("household_notification_subscriptions", "daily_reminder_time"):
        op.add_column(
            "household_notification_subscriptions",
            sa.Column("daily_reminder_time", sa.Time(), nullable=False, server_default="08:00:00"),
        )
    if not _has_column("household_notification_subscriptions", "shopping_window_days"):
        op.add_column(
            "household_notification_subscriptions",
            sa.Column("shopping_window_days", sa.Integer(), nullable=False, server_default="3"),
        )
    if not _has_column("household_notification_subscriptions", "timezone"):
        op.add_column(
            "household_notification_subscriptions",
            sa.Column("timezone", sa.String(length=64), nullable=False, server_default="Europe/Paris"),
        )
    if not _has_column("household_notification_subscriptions", "last_reminder_sent_at"):
        op.add_column(
            "household_notification_subscriptions",
            sa.Column("last_reminder_sent_at", sa.DateTime(timezone=True), nullable=True),
        )

    op.execute(
        """
        UPDATE household_notification_subscriptions AS sub
        SET
            daily_reminder_time = ts.daily_reminder_time,
            shopping_window_days = ts.shopping_window_days,
            timezone = ts.timezone
        FROM telegram_settings AS ts
        WHERE ts.household_id = sub.household_id
        """
    )


def downgrade() -> None:
    if _has_column("household_notification_subscriptions", "last_reminder_sent_at"):
        op.drop_column("household_notification_subscriptions", "last_reminder_sent_at")
    if _has_column("household_notification_subscriptions", "timezone"):
        op.drop_column("household_notification_subscriptions", "timezone")
    if _has_column("household_notification_subscriptions", "shopping_window_days"):
        op.drop_column("household_notification_subscriptions", "shopping_window_days")
    if _has_column("household_notification_subscriptions", "daily_reminder_time"):
        op.drop_column("household_notification_subscriptions", "daily_reminder_time")
