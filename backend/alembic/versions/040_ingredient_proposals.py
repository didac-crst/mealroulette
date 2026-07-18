"""Ingredient proposals for governed catalog requests.

Revision ID: 040_ingredient_proposals
Revises: 039_telegram_login_otp
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect, text
from sqlalchemy.dialects import postgresql

revision: str = "040_ingredient_proposals"
down_revision: Union[str, Sequence[str], None] = "039_telegram_login_otp"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(inspector: sa.Inspector, table: str, column: str) -> bool:
    return any(col["name"] == column for col in inspector.get_columns(table))


def _drop_legacy_umbrella_table(bind) -> None:
    """Remove the deferred umbrella schema if present (never shipped on main)."""
    op.drop_table("ingredient_proposals")
    # Old umbrella used a Postgres enum; drop it if nothing else references it.
    bind.execute(text("DROP TYPE IF EXISTS ingredient_proposal_status"))


def _create_indexes() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing = {idx["name"] for idx in inspector.get_indexes("ingredient_proposals")}
    wanted = {
        "ix_ingredient_proposals_normalized_name": ["normalized_name"],
        "ix_ingredient_proposals_resolution_status": ["resolution_status"],
        "ix_ingredient_proposals_proposed_by_user_id": ["proposed_by_user_id"],
        "ix_ingredient_proposals_household_id": ["household_id"],
        "ix_ingredient_proposals_resolved_ingredient_id": ["resolved_ingredient_id"],
        "ix_ingredient_proposals_norm_locale_status": [
            "normalized_name",
            "source_locale",
            "resolution_status",
        ],
    }
    for name, columns in wanted.items():
        if name not in existing:
            op.create_index(name, "ingredient_proposals", columns)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if inspector.has_table("ingredient_proposals"):
        if _has_column(inspector, "ingredient_proposals", "normalized_name"):
            # Local volumes may already have the Phase 16C table.
            _create_indexes()
            return
        # Local volumes may still have the deferred umbrella table shape.
        _drop_legacy_umbrella_table(bind)

    op.create_table(
        "ingredient_proposals",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("proposed_name", sa.String(length=128), nullable=False),
        sa.Column("normalized_name", sa.String(length=128), nullable=False),
        sa.Column("source_locale", sa.String(length=16), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("culinary_context", sa.Text(), nullable=True),
        sa.Column("suggested_food_group_id", sa.String(length=64), nullable=True),
        sa.Column("suggested_family_id", sa.String(length=64), nullable=True),
        sa.Column("suggested_storage_class", sa.String(length=32), nullable=True),
        sa.Column("suggested_product_form", sa.String(length=32), nullable=True),
        sa.Column("suggested_preservation", sa.String(length=32), nullable=True),
        sa.Column("resolution_status", sa.String(length=32), nullable=False),
        sa.Column("resolution_type", sa.String(length=32), nullable=True),
        sa.Column("resolved_ingredient_id", sa.Integer(), nullable=True),
        sa.Column("proposed_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("household_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("source_reference_type", sa.String(length=64), nullable=True),
        sa.Column("source_reference_id", sa.String(length=128), nullable=True),
        sa.Column("model_provider", sa.String(length=64), nullable=True),
        sa.Column("model_name", sa.String(length=128), nullable=True),
        sa.Column("model_confidence", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("model_reasoning_summary", sa.Text(), nullable=True),
        sa.Column("reviewed_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["household_id"], ["households.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["proposed_by_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resolved_ingredient_id"], ["ingredients.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["suggested_family_id"], ["ingredient_families.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["suggested_food_group_id"], ["food_groups.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_indexes()


def downgrade() -> None:
    bind = op.get_bind()
    if not inspect(bind).has_table("ingredient_proposals"):
        return
    for name in (
        "ix_ingredient_proposals_norm_locale_status",
        "ix_ingredient_proposals_resolved_ingredient_id",
        "ix_ingredient_proposals_household_id",
        "ix_ingredient_proposals_proposed_by_user_id",
        "ix_ingredient_proposals_resolution_status",
        "ix_ingredient_proposals_normalized_name",
    ):
        op.drop_index(name, table_name="ingredient_proposals")
    op.drop_table("ingredient_proposals")
