"""Add household tenancy identity tables and migrate users to UUID.

Revision ID: 033_household_tenancy_identity
Revises: 032_reroll_history
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "033_household_tenancy_identity"
down_revision: Union[str, Sequence[str], None] = "032_reroll_history"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_HOUSEHOLD_ID = "00000000-0000-4000-8000-000000000001"
DEFAULT_HOUSEHOLD_NAME = "Default household"

household_role = postgresql.ENUM(
    "household_admin",
    "household_member",
    name="household_role",
    create_type=False,
)
platform_role = postgresql.ENUM(
    "platform_admin",
    name="platform_role",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    household_role.create(bind, checkfirst=True)
    platform_role.create(bind, checkfirst=True)

    op.create_table(
        "households",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute(
        sa.text(
            "INSERT INTO households (id, name) VALUES (:id, :name)"
        ).bindparams(id=DEFAULT_HOUSEHOLD_ID, name=DEFAULT_HOUSEHOLD_NAME)
    )

    op.create_table(
        "_user_id_migration",
        sa.Column("old_id", sa.Integer(), nullable=False),
        sa.Column("new_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("old_id"),
        sa.UniqueConstraint("new_id"),
    )
    op.execute(
        sa.text(
            """
            INSERT INTO _user_id_migration (old_id, new_id)
            SELECT id, gen_random_uuid()
            FROM users
            """
        )
    )

    op.create_table(
        "users_uuid",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", postgresql.ENUM("admin", "user", name="user_role", create_type=False), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_uuid_email"), "users_uuid", ["email"], unique=True)
    op.create_index(op.f("ix_users_uuid_username"), "users_uuid", ["username"], unique=True)
    op.execute(
        sa.text(
            """
            INSERT INTO users_uuid (id, username, email, password_hash, role, active, created_at, updated_at)
            SELECT m.new_id, u.username, u.email, u.password_hash, u.role, u.active, u.created_at, u.updated_at
            FROM users u
            JOIN _user_id_migration m ON m.old_id = u.id
            """
        )
    )

    op.add_column("refresh_tokens", sa.Column("user_uuid", postgresql.UUID(as_uuid=True), nullable=True))
    op.execute(
        sa.text(
            """
            UPDATE refresh_tokens rt
            SET user_uuid = m.new_id
            FROM _user_id_migration m
            WHERE rt.user_id = m.old_id
            """
        )
    )
    op.drop_constraint("refresh_tokens_user_id_fkey", "refresh_tokens", type_="foreignkey")
    op.drop_index(op.f("ix_refresh_tokens_user_id"), table_name="refresh_tokens")
    op.drop_column("refresh_tokens", "user_id")
    op.alter_column("refresh_tokens", "user_uuid", new_column_name="user_id", nullable=False)
    op.create_index(op.f("ix_refresh_tokens_user_id"), "refresh_tokens", ["user_id"], unique=False)

    op.add_column("cooking_timer_alerts", sa.Column("user_uuid", postgresql.UUID(as_uuid=True), nullable=True))
    op.execute(
        sa.text(
            """
            UPDATE cooking_timer_alerts cta
            SET user_uuid = m.new_id
            FROM _user_id_migration m
            WHERE cta.user_id = m.old_id
            """
        )
    )
    op.drop_constraint("cooking_timer_alerts_user_id_fkey", "cooking_timer_alerts", type_="foreignkey")
    op.drop_column("cooking_timer_alerts", "user_id")
    op.alter_column("cooking_timer_alerts", "user_uuid", new_column_name="user_id", nullable=False)

    op.drop_table("users")
    op.rename_table("users_uuid", "users")
    op.execute("ALTER INDEX ix_users_uuid_email RENAME TO ix_users_email")
    op.execute("ALTER INDEX ix_users_uuid_username RENAME TO ix_users_username")
    op.create_foreign_key(
        "refresh_tokens_user_id_fkey",
        "refresh_tokens",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "cooking_timer_alerts_user_id_fkey",
        "cooking_timer_alerts",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_table(
        "household_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("household_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", household_role, nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["household_id"], ["households.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("household_id", "user_id", name="uq_household_memberships_household_user"),
    )
    op.create_index(
        op.f("ix_household_memberships_household_id"),
        "household_memberships",
        ["household_id"],
        unique=False,
    )
    op.create_index(op.f("ix_household_memberships_user_id"), "household_memberships", ["user_id"], unique=False)

    op.create_table(
        "user_platform_roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", platform_role, nullable=False),
        sa.Column("granted_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "role", name="uq_user_platform_roles_user_role"),
    )
    op.create_index(op.f("ix_user_platform_roles_user_id"), "user_platform_roles", ["user_id"], unique=False)

    op.execute(
        sa.text(
            """
            INSERT INTO household_memberships (
                id, household_id, user_id, role, active, joined_at, created_at, updated_at
            )
            SELECT
                gen_random_uuid(),
                CAST(:household_id AS uuid),
                u.id,
                CASE WHEN u.role = 'admin' THEN 'household_admin'::household_role ELSE 'household_member'::household_role END,
                true,
                u.created_at,
                u.created_at,
                u.updated_at
            FROM users u
            """
        ).bindparams(household_id=DEFAULT_HOUSEHOLD_ID)
    )
    op.execute(
        sa.text(
            """
            INSERT INTO user_platform_roles (id, user_id, role, granted_at)
            SELECT gen_random_uuid(), u.id, 'platform_admin'::platform_role, u.created_at
            FROM users u
            WHERE u.role = 'admin'
            """
        )
    )

    op.drop_table("_user_id_migration")


def downgrade() -> None:
    raise NotImplementedError("Downgrade is not supported for UUID user migration.")
