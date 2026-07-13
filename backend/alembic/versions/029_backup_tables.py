"""Add backup settings and run tracking.

Revision ID: 029_backup_tables
Revises: 028_taxonomy_tables
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "029_backup_tables"
down_revision: Union[str, Sequence[str], None] = "028_taxonomy_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

backup_type = postgresql.ENUM("json_export", "pg_dump", name="backup_type", create_type=False)
backup_run_status = postgresql.ENUM(
    "running", "succeeded", "failed", name="backup_run_status", create_type=False
)


def _ensure_enum(name: str, values: str) -> None:
    op.execute(
        f"""
        DO $$ BEGIN
            CREATE TYPE {name} AS ENUM ({values});
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )


def upgrade() -> None:
    _ensure_enum("backup_type", "'json_export', 'pg_dump'")
    _ensure_enum("backup_run_status", "'running', 'succeeded', 'failed'")

    op.create_table(
        "backup_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("run_time", sa.Time(), nullable=False, server_default=sa.text("'03:00:00'")),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="Europe/Paris"),
        sa.Column("retention_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("backup_path", sa.String(length=255), nullable=False, server_default="/backups"),
        sa.Column("include_json_export", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("include_pg_dump", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("last_backup_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "backup_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("backup_type", backup_type, nullable=False),
        sa.Column("status", backup_run_status, nullable=False),
        sa.Column("file_path", sa.String(length=512), nullable=True),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.execute(
        """
        INSERT INTO backup_settings (id, enabled, run_time, timezone, retention_days, backup_path,
            include_json_export, include_pg_dump)
        VALUES (1, false, '03:00:00', 'Europe/Paris', 30, '/backups', true, false)
        ON CONFLICT (id) DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_table("backup_runs")
    op.drop_table("backup_settings")
    backup_run_status.drop(op.get_bind(), checkfirst=True)
    backup_type.drop(op.get_bind(), checkfirst=True)
