"""Public recipe catalog foundations.

Revision ID: 041_public_catalog
Revises: 040_ingredient_proposals
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "041_public_catalog"
down_revision: Union[str, Sequence[str], None] = "040_ingredient_proposals"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "public_recipes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("originating_household_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("originating_dish_id", sa.Integer(), nullable=False),
        sa.Column("originating_recipe_id", sa.Integer(), nullable=False),
        sa.Column("current_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("submitted_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reviewed_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["originating_household_id"], ["households.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["originating_dish_id"], ["dishes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["originating_recipe_id"], ["recipes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["submitted_by_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("originating_recipe_id", name="uq_public_recipes_originating_recipe_id"),
    )
    op.create_index("ix_public_recipes_originating_household_id", "public_recipes", ["originating_household_id"])
    op.create_index("ix_public_recipes_originating_dish_id", "public_recipes", ["originating_dish_id"])
    op.create_index("ix_public_recipes_originating_recipe_id", "public_recipes", ["originating_recipe_id"])
    op.create_index("ix_public_recipes_status", "public_recipes", ["status"])

    op.create_table(
        "public_recipe_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("public_recipe_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("snapshot_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["public_recipe_id"], ["public_recipes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "public_recipe_id",
            "version_number",
            name="uq_public_recipe_versions_recipe_version",
        ),
    )
    op.create_index("ix_public_recipe_versions_public_recipe_id", "public_recipe_versions", ["public_recipe_id"])

    op.create_foreign_key(
        "fk_public_recipes_current_version_id",
        "public_recipes",
        "public_recipe_versions",
        ["current_version_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column(
        "recipes",
        sa.Column("derived_from_public_recipe_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "recipes",
        sa.Column("derived_from_public_version_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_recipes_derived_from_public_recipe_id",
        "recipes",
        "public_recipes",
        ["derived_from_public_recipe_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_recipes_derived_from_public_version_id",
        "recipes",
        "public_recipe_versions",
        ["derived_from_public_version_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_recipes_derived_from_public_recipe_id",
        "recipes",
        ["derived_from_public_recipe_id"],
    )
    op.create_index(
        "ix_recipes_derived_from_public_version_id",
        "recipes",
        ["derived_from_public_version_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_recipes_derived_from_public_version_id", table_name="recipes")
    op.drop_index("ix_recipes_derived_from_public_recipe_id", table_name="recipes")
    op.drop_constraint("fk_recipes_derived_from_public_version_id", "recipes", type_="foreignkey")
    op.drop_constraint("fk_recipes_derived_from_public_recipe_id", "recipes", type_="foreignkey")
    op.drop_column("recipes", "derived_from_public_version_id")
    op.drop_column("recipes", "derived_from_public_recipe_id")

    op.drop_constraint("fk_public_recipes_current_version_id", "public_recipes", type_="foreignkey")
    op.drop_index("ix_public_recipe_versions_public_recipe_id", table_name="public_recipe_versions")
    op.drop_table("public_recipe_versions")
    op.drop_index("ix_public_recipes_status", table_name="public_recipes")
    op.drop_index("ix_public_recipes_originating_recipe_id", table_name="public_recipes")
    op.drop_index("ix_public_recipes_originating_dish_id", table_name="public_recipes")
    op.drop_index("ix_public_recipes_originating_household_id", table_name="public_recipes")
    op.drop_table("public_recipes")
