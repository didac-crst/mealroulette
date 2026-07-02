"""Add catalog tables (units, tags, ingredients, dishes, recipes).

Revision ID: 003_catalog
Revises: 002_users
Create Date: 2026-07-02 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_catalog"
down_revision: Union[str, Sequence[str], None] = "002_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

unit_dimension = sa.Enum("mass", "volume", "count", name="unit_dimension")
seasonality_mode = sa.Enum("all_year", "seasonal", "avoid", "strict", name="seasonality_mode")
seasonality_strength = sa.Enum("neutral", "low", "medium", "strong", name="seasonality_strength")
conversion_confidence = sa.Enum("approximate", "measured", name="conversion_confidence")


def upgrade() -> None:
    op.create_table(
        "units",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("dimension", unit_dimension, nullable=False),
        sa.Column("conversion_to_base", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("symbol"),
    )

    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("family", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("family", "name", name="uq_tags_family_name"),
    )

    op.create_table(
        "dishes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("default_servings", sa.Integer(), nullable=True),
        sa.Column("prep_time_minutes", sa.Integer(), nullable=True),
        sa.Column("cook_time_minutes", sa.Integer(), nullable=True),
        sa.Column("difficulty", sa.String(length=32), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_dishes_name"), "dishes", ["name"], unique=True)

    op.create_table(
        "dish_seasonality",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("dish_id", sa.Integer(), nullable=False),
        sa.Column("seasonality_mode", seasonality_mode, nullable=False),
        sa.Column(
            "preferred_months",
            postgresql.ARRAY(sa.Integer()),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
        sa.Column(
            "allowed_months",
            postgresql.ARRAY(sa.Integer()),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
        sa.Column(
            "excluded_months",
            postgresql.ARRAY(sa.Integer()),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
        sa.Column("seasonality_strength", seasonality_strength, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["dish_id"], ["dishes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dish_id"),
    )

    op.create_table(
        "dish_tags",
        sa.Column("dish_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["dish_id"], ["dishes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("dish_id", "tag_id"),
    )

    op.create_table(
        "ingredients",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("canonical_name", sa.String(length=128), nullable=False),
        sa.Column("display_name", sa.String(length=128), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=True),
        sa.Column("default_unit_id", sa.Integer(), nullable=True),
        sa.Column(
            "default_dimension",
            sa.Enum("mass", "volume", "count", name="unit_dimension", create_type=False),
            nullable=True,
        ),
        sa.Column("pantry_item", sa.Boolean(), nullable=False),
        sa.Column("season_start_month", sa.Integer(), nullable=True),
        sa.Column("season_end_month", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["default_unit_id"], ["units.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ingredients_canonical_name"), "ingredients", ["canonical_name"], unique=True)

    op.create_table(
        "recipes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("dish_id", sa.Integer(), nullable=False),
        sa.Column("variant_name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_thermomix", sa.Boolean(), nullable=False),
        sa.Column("source_url", sa.String(length=512), nullable=True),
        sa.Column("servings", sa.Integer(), nullable=True),
        sa.Column("prep_time_minutes", sa.Integer(), nullable=True),
        sa.Column("cook_time_minutes", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["dish_id"], ["dishes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dish_id", "variant_name", name="uq_recipes_dish_variant"),
    )
    op.create_index(op.f("ix_recipes_dish_id"), "recipes", ["dish_id"], unique=False)

    op.create_table(
        "ingredient_aliases",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ingredient_id", sa.Integer(), nullable=False),
        sa.Column("alias", sa.String(length=128), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["ingredient_id"], ["ingredients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("alias", name="uq_ingredient_aliases_alias"),
    )
    op.create_index(op.f("ix_ingredient_aliases_alias"), "ingredient_aliases", ["alias"], unique=False)
    op.create_index(
        op.f("ix_ingredient_aliases_ingredient_id"), "ingredient_aliases", ["ingredient_id"], unique=False
    )

    op.create_table(
        "ingredient_unit_conversions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ingredient_id", sa.Integer(), nullable=False),
        sa.Column("from_unit_id", sa.Integer(), nullable=False),
        sa.Column("to_unit_id", sa.Integer(), nullable=False),
        sa.Column("factor", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("confidence", conversion_confidence, nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["from_unit_id"], ["units.id"]),
        sa.ForeignKeyConstraint(["ingredient_id"], ["ingredients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["to_unit_id"], ["units.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_ingredient_unit_conversions_ingredient_id"),
        "ingredient_unit_conversions",
        ["ingredient_id"],
        unique=False,
    )

    op.create_table(
        "recipe_ingredients",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recipe_id", sa.Integer(), nullable=False),
        sa.Column("ingredient_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("unit_id", sa.Integer(), nullable=True),
        sa.Column("optional", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["ingredient_id"], ["ingredients.id"]),
        sa.ForeignKeyConstraint(["recipe_id"], ["recipes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["unit_id"], ["units.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_recipe_ingredients_ingredient_id"), "recipe_ingredients", ["ingredient_id"], unique=False
    )
    op.create_index(op.f("ix_recipe_ingredients_recipe_id"), "recipe_ingredients", ["recipe_id"], unique=False)

    op.create_table(
        "recipe_steps",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recipe_id", sa.Integer(), nullable=False),
        sa.Column("step_number", sa.Integer(), nullable=False),
        sa.Column("instruction", sa.Text(), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("temperature", sa.String(length=64), nullable=True),
        sa.Column("timer_seconds", sa.Integer(), nullable=True),
        sa.Column("is_thermomix_step", sa.Boolean(), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["recipe_id"], ["recipes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("recipe_id", "step_number", name="uq_recipe_steps_recipe_number"),
    )
    op.create_index(op.f("ix_recipe_steps_recipe_id"), "recipe_steps", ["recipe_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_recipe_steps_recipe_id"), table_name="recipe_steps")
    op.drop_table("recipe_steps")
    op.drop_index(op.f("ix_recipe_ingredients_recipe_id"), table_name="recipe_ingredients")
    op.drop_index(op.f("ix_recipe_ingredients_ingredient_id"), table_name="recipe_ingredients")
    op.drop_table("recipe_ingredients")
    op.drop_index(
        op.f("ix_ingredient_unit_conversions_ingredient_id"), table_name="ingredient_unit_conversions"
    )
    op.drop_table("ingredient_unit_conversions")
    op.drop_index(op.f("ix_ingredient_aliases_ingredient_id"), table_name="ingredient_aliases")
    op.drop_index(op.f("ix_ingredient_aliases_alias"), table_name="ingredient_aliases")
    op.drop_table("ingredient_aliases")
    op.drop_index(op.f("ix_recipes_dish_id"), table_name="recipes")
    op.drop_table("recipes")
    op.drop_index(op.f("ix_ingredients_canonical_name"), table_name="ingredients")
    op.drop_table("ingredients")
    op.drop_table("dish_tags")
    op.drop_table("dish_seasonality")
    op.drop_index(op.f("ix_dishes_name"), table_name="dishes")
    op.drop_table("dishes")
    op.drop_table("tags")
    op.drop_table("units")
    conversion_confidence.drop(op.get_bind(), checkfirst=True)
    seasonality_strength.drop(op.get_bind(), checkfirst=True)
    seasonality_mode.drop(op.get_bind(), checkfirst=True)
    unit_dimension.drop(op.get_bind(), checkfirst=True)
