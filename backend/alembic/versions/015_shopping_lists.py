"""Add shopping lists and shopping list items.

Revision ID: 015_shopping_lists
Revises: 014_review_saved_at
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "015_shopping_lists"
down_revision: Union[str, Sequence[str], None] = "014_review_saved_at"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

shopping_list_status = postgresql.ENUM(
    "draft",
    "active",
    "completed",
    "archived",
    name="shopping_list_status",
    create_type=False,
)


def upgrade() -> None:
    shopping_list_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "shopping_lists",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("from_date", sa.Date(), nullable=False),
        sa.Column("to_date", sa.Date(), nullable=False),
        sa.Column(
            "status",
            shopping_list_status,
            nullable=False,
            server_default="active",
        ),
        sa.Column("exclude_pantry", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("from_date <= to_date", name="ck_shopping_lists_date_range"),
    )
    op.create_index("ix_shopping_lists_from_date", "shopping_lists", ["from_date"])

    op.create_table(
        "shopping_list_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("shopping_list_id", sa.Integer(), nullable=False),
        sa.Column("ingredient_id", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(length=128), nullable=False),
        sa.Column("quantity", sa.Numeric(12, 4), nullable=False),
        sa.Column("unit_id", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("checked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("approximate", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("optional", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("source_meal_plan_item_ids_json", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["ingredient_id"], ["ingredients.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["shopping_list_id"], ["shopping_lists.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["unit_id"], ["units.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("quantity > 0", name="ck_shopping_list_items_quantity_positive"),
    )
    op.create_index(
        "ix_shopping_list_items_shopping_list_id",
        "shopping_list_items",
        ["shopping_list_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_shopping_list_items_shopping_list_id", table_name="shopping_list_items")
    op.drop_table("shopping_list_items")
    op.drop_index("ix_shopping_lists_from_date", table_name="shopping_lists")
    op.drop_table("shopping_lists")
    shopping_list_status.drop(op.get_bind(), checkfirst=True)
