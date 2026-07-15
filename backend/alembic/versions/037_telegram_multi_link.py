"""Allow one Telegram chat to link many MealRoulette users.

Revision ID: 037_telegram_multi_link
Revises: 036_greenfield_household
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "037_telegram_multi_link"
down_revision: Union[str, Sequence[str], None] = "036_greenfield_household"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("uq_telegram_user_links_chat_id", "telegram_user_links", type_="unique")
    op.create_index("ix_telegram_user_links_chat_id", "telegram_user_links", ["chat_id"])


def downgrade() -> None:
    op.drop_index("ix_telegram_user_links_chat_id", table_name="telegram_user_links")
    op.create_unique_constraint("uq_telegram_user_links_chat_id", "telegram_user_links", ["chat_id"])
