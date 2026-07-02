"""Restrict dish course to starter, main, dessert.

Revision ID: 010_dish_course_simplify
Revises: 009_dish_image_url
"""

from typing import Sequence, Union

from alembic import op

revision: str = "010_dish_course_simplify"
down_revision: Union[str, Sequence[str], None] = "009_dish_image_url"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "UPDATE dishes SET course = NULL WHERE course::text IN ('side', 'snack', 'sauce_condiment')"
    )
    op.execute("ALTER TYPE dish_course RENAME TO dish_course_old")
    op.execute("CREATE TYPE dish_course AS ENUM ('starter', 'main', 'dessert')")
    op.execute(
        """
        ALTER TABLE dishes
        ALTER COLUMN course TYPE dish_course
        USING course::text::dish_course
        """
    )
    op.execute("DROP TYPE dish_course_old")


def downgrade() -> None:
    op.execute("ALTER TYPE dish_course RENAME TO dish_course_new")
    op.execute(
        """
        CREATE TYPE dish_course AS ENUM (
            'main', 'side', 'starter', 'dessert', 'snack', 'sauce_condiment'
        )
        """
    )
    op.execute(
        """
        ALTER TABLE dishes
        ALTER COLUMN course TYPE dish_course
        USING course::text::dish_course
        """
    )
    op.execute("DROP TYPE dish_course_new")
