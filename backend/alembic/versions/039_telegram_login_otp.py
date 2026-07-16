"""Telegram login one-time passwords.

Revision ID: 039_telegram_login_otp
Revises: 038_telegram_user_identity_unique
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision: str = "039_telegram_login_otp"
down_revision: Union[str, Sequence[str], None] = "038_telegram_user_identity_unique"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if inspect(bind).has_table("telegram_login_otps"):
        # Local volumes may already have this table from the deferred umbrella branch.
        return

    op.create_table(
        "telegram_login_otps",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_telegram_login_otps_user_id"),
    )
    op.create_index("ix_telegram_login_otps_user_id", "telegram_login_otps", ["user_id"])


def downgrade() -> None:
    bind = op.get_bind()
    if not inspect(bind).has_table("telegram_login_otps"):
        return
    op.drop_index("ix_telegram_login_otps_user_id", table_name="telegram_login_otps")
    op.drop_table("telegram_login_otps")
