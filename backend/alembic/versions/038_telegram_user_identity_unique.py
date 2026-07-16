"""Unique Telegram identity per MealRoulette user link.

Revision ID: 038_telegram_user_identity_unique
Revises: 037_telegram_user_links_and_subscriptions
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "038_telegram_user_identity_unique"
down_revision: Union[str, Sequence[str], None] = "037_telegram_user_links_and_subscriptions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    duplicates = bind.execute(
        sa.text(
            """
            SELECT telegram_user_id, COUNT(*) AS cnt
            FROM telegram_user_links
            WHERE telegram_user_id IS NOT NULL
            GROUP BY telegram_user_id
            HAVING COUNT(*) > 1
            ORDER BY telegram_user_id
            """
        )
    ).fetchall()
    if duplicates:
        sample = ", ".join(f"{row.telegram_user_id} ({row.cnt})" for row in duplicates[:10])
        raise RuntimeError(
            "Cannot apply unique telegram_user_id constraint: duplicate Telegram identities "
            f"exist in telegram_user_links ({len(duplicates)} identities). "
            "Manually reconcile so each non-null telegram_user_id maps to one MealRoulette user, "
            f"then re-run the migration. Examples: {sample}"
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
