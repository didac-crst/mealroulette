"""Scheduler settings and planning rules for automatic meal roulette.

Revision ID: 020_scheduler_planning_rules
Revises: 019_telegram_settings
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

from mealroulette.data.default_planning_rules import DEFAULT_PLANNING_RULES_JSON, DEFAULT_PLANNING_RULE_NAME

revision: str = "020_scheduler_planning_rules"
down_revision: Union[str, Sequence[str], None] = "019_telegram_settings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "planning_rules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("rules_json", JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_planning_rules_name"),
    )

    planning_rules = sa.table(
        "planning_rules",
        sa.column("id", sa.Integer),
        sa.column("name", sa.String),
        sa.column("active", sa.Boolean),
        sa.column("rules_json", JSONB),
    )
    op.bulk_insert(
        planning_rules,
        [
            {
                "id": 1,
                "name": DEFAULT_PLANNING_RULE_NAME,
                "active": True,
                "rules_json": DEFAULT_PLANNING_RULES_JSON,
            }
        ],
    )
    op.execute(sa.text("SELECT setval('planning_rules_id_seq', (SELECT MAX(id) FROM planning_rules))"))

    op.create_table(
        "scheduler_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("run_weekday", sa.Integer(), nullable=False, server_default=sa.text("4")),
        sa.Column("run_time", sa.Time(), nullable=False, server_default=sa.text("'18:00:00'")),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="Europe/Paris"),
        sa.Column("target_week_offset", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("notify_telegram", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notify_planning_days", sa.Integer(), nullable=False, server_default=sa.text("7")),
        sa.Column("last_roulette_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("run_weekday >= 0 AND run_weekday <= 6", name="ck_scheduler_run_weekday"),
        sa.CheckConstraint(
            "target_week_offset >= 0 AND target_week_offset <= 4",
            name="ck_scheduler_target_week_offset",
        ),
        sa.CheckConstraint(
            "notify_planning_days >= 1 AND notify_planning_days <= 14",
            name="ck_scheduler_notify_planning_days",
        ),
    )
    op.execute(sa.text("INSERT INTO scheduler_settings (id, enabled) VALUES (1, false)"))


def downgrade() -> None:
    op.drop_table("scheduler_settings")
    op.drop_table("planning_rules")
