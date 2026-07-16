"""Unique Telegram identity per MealRoulette user link.

Revision ID: 038_telegram_user_identity_unique
Revises: 037_telegram_user_links_and_subscriptions
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "038_telegram_user_identity_unique"
down_revision: Union[str, Sequence[str], None] = "037_telegram_user_links_and_subscriptions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Keep the newest link when the same Telegram identity was previously attached to
    # multiple MealRoulette users (should not happen after 15E, but be safe for upgrades).
    op.execute(
        """
        DELETE FROM telegram_user_links AS older
        USING telegram_user_links AS newer
        WHERE older.telegram_user_id IS NOT NULL
          AND newer.telegram_user_id IS NOT NULL
          AND older.telegram_user_id = newer.telegram_user_id
          AND older.linked_at < newer.linked_at
        """
    )
    op.execute(
        """
        DELETE FROM telegram_user_links AS older
        USING telegram_user_links AS newer
        WHERE older.telegram_user_id IS NOT NULL
          AND newer.telegram_user_id IS NOT NULL
          AND older.telegram_user_id = newer.telegram_user_id
          AND older.id < newer.id
          AND older.linked_at = newer.linked_at
        """
    )
    op.create_index(
        "uq_telegram_user_links_telegram_user_id",
        "telegram_user_links",
        ["telegram_user_id"],
        unique=True,
        postgresql_where="telegram_user_id IS NOT NULL",
    )


def downgrade() -> None:
    op.drop_index("uq_telegram_user_links_telegram_user_id", table_name="telegram_user_links")
