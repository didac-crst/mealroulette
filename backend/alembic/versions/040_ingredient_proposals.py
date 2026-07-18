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

_PHASE_16C_REQUIRED_COLUMNS = frozenset(
    {
        "normalized_name",
        "resolution_status",
        "proposed_name",
        "source_locale",
        "proposed_by_user_id",
    }
)


def _column_names(inspector: sa.Inspector, table: str) -> set[str]:
    return {col["name"] for col in inspector.get_columns(table)}


def _has_pg_type(bind, typname: str) -> bool:
    return (
        bind.execute(
            text("SELECT 1 FROM pg_type WHERE typname = :typname"),
            {"typname": typname},
        ).scalar()
        is not None
    )


def _is_phase_16c_shape(columns: set[str]) -> bool:
    return _PHASE_16C_REQUIRED_COLUMNS.issubset(columns)


def _is_known_legacy_umbrella_shape(bind, columns: set[str]) -> bool:
    """Detect the never-shipped local-only umbrella table.

    That shape lacked ``normalized_name`` / ``resolution_status`` and used the
    ``ingredient_proposal_status`` Postgres enum (often exposed as ``status``).
    """
    if "normalized_name" in columns or "resolution_status" in columns:
        return False
    if _has_pg_type(bind, "ingredient_proposal_status"):
        return True
    return "status" in columns and "proposed_name" in columns


def _drop_legacy_umbrella_table(bind) -> None:
    """Remove the deferred umbrella schema if present (never shipped on main)."""
    op.drop_table("ingredient_proposals")
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
        columns = _column_names(inspector, "ingredient_proposals")
        if _is_phase_16c_shape(columns):
            # Local volumes may already have the Phase 16C table.
            _create_indexes()
            return
        if _is_known_legacy_umbrella_shape(bind, columns):
            _drop_legacy_umbrella_table(bind)
        else:
            raise RuntimeError(
                "Refusing to modify ingredient_proposals: table exists with an unknown schema. "
                "Expected either the Phase 16C shape (normalized_name + resolution_status) or the "
                "known local-only umbrella shape (status enum / no normalized_name). "
                f"Found columns: {sorted(columns)}. Inspect the table and migrate or rename it "
                "manually before re-running this revision."
            )

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
