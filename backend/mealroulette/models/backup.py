from datetime import datetime, time

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, Integer, String, Text, Time, func
from sqlalchemy.orm import Mapped, mapped_column

from mealroulette.db.base import Base
from mealroulette.models.enums import BackupRunStatus, BackupType

BACKUP_SETTINGS_ID = 1


class BackupSettings(Base):
    __tablename__ = "backup_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    run_time: Mapped[time] = mapped_column(Time, nullable=False, default=time(3, 0))
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="Europe/Paris")
    retention_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    backup_path: Mapped[str] = mapped_column(String(255), nullable=False, default="/backups")
    include_json_export: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    include_pg_dump: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_backup_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class BackupRun(Base):
    __tablename__ = "backup_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    backup_type: Mapped[BackupType] = mapped_column(Enum(BackupType, name="backup_type"), nullable=False)
    status: Mapped[BackupRunStatus] = mapped_column(Enum(BackupRunStatus, name="backup_run_status"), nullable=False)
    file_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
