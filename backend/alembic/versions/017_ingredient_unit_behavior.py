"""Ingredient unit behavior and conversion approval.

Revision ID: 017_ingredient_unit_behavior
Revises: 016_shopping_contributions
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "017_ingredient_unit_behavior"
down_revision: Union[str, Sequence[str], None] = "016_shopping_contributions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

aggregation_strategy = postgresql.ENUM(
    "strict_same_dimension",
    "prefer_mass",
    "prefer_volume",
    "prefer_count",
    "allow_approximate_conversion",
    "never_convert_count",
    name="aggregation_strategy",
    create_type=False,
)

conversion_source = postgresql.ENUM(
    "manual",
    "seed",
    "llm_suggested",
    name="conversion_source",
    create_type=False,
)


def upgrade() -> None:
    op.execute(
        """
        DO $$ BEGIN
            ALTER TYPE conversion_confidence ADD VALUE IF NOT EXISTS 'exact';
            ALTER TYPE conversion_confidence ADD VALUE IF NOT EXISTS 'high';
            ALTER TYPE conversion_confidence ADD VALUE IF NOT EXISTS 'medium';
            ALTER TYPE conversion_confidence ADD VALUE IF NOT EXISTS 'low';
            ALTER TYPE conversion_confidence ADD VALUE IF NOT EXISTS 'not_recommended';
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
        """
    )

    aggregation_strategy.create(op.get_bind(), checkfirst=True)
    conversion_source.create(op.get_bind(), checkfirst=True)

    op.add_column("ingredients", sa.Column("family", sa.String(length=64), nullable=True))
    op.add_column("ingredients", sa.Column("preferred_shopping_unit_id", sa.Integer(), nullable=True))
    op.add_column("ingredients", sa.Column("aggregation_unit_id", sa.Integer(), nullable=True))
    op.add_column(
        "ingredients",
        sa.Column("aggregation_strategy", aggregation_strategy, nullable=True),
    )
    op.create_foreign_key(
        "fk_ingredients_preferred_shopping_unit_id",
        "ingredients",
        "units",
        ["preferred_shopping_unit_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_ingredients_aggregation_unit_id",
        "ingredients",
        "units",
        ["aggregation_unit_id"],
        ["id"],
    )

    op.add_column(
        "ingredient_unit_conversions",
        sa.Column("approved", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "ingredient_unit_conversions",
        sa.Column("source", conversion_source, nullable=True),
    )
    op.alter_column("ingredient_unit_conversions", "approved", server_default=None)


def downgrade() -> None:
    op.drop_column("ingredient_unit_conversions", "source")
    op.drop_column("ingredient_unit_conversions", "approved")
    op.drop_constraint("fk_ingredients_aggregation_unit_id", "ingredients", type_="foreignkey")
    op.drop_constraint("fk_ingredients_preferred_shopping_unit_id", "ingredients", type_="foreignkey")
    op.drop_column("ingredients", "aggregation_strategy")
    op.drop_column("ingredients", "aggregation_unit_id")
    op.drop_column("ingredients", "preferred_shopping_unit_id")
    op.drop_column("ingredients", "family")
    conversion_source.drop(op.get_bind(), checkfirst=True)
    aggregation_strategy.drop(op.get_bind(), checkfirst=True)
