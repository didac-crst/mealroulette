from datetime import datetime, time
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BackupSettingsPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    enabled: bool
    run_time: str
    timezone: str
    retention_days: int
    backup_path: str
    include_json_export: bool
    include_pg_dump: bool
    last_backup_at: datetime | None
    last_error: str | None


class BackupSettingsUpdateRequest(BaseModel):
    enabled: bool | None = None
    run_time: time | None = None
    timezone: str | None = None
    retention_days: int | None = Field(default=None, ge=1, le=3650)
    backup_path: str | None = None
    include_json_export: bool | None = None
    include_pg_dump: bool | None = None

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str | None) -> str | None:
        if value is None:
            return value
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"Unknown timezone: {value}") from exc
        return value


class BackupRunPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    backup_type: str
    status: str
    file_path: str | None
    file_size_bytes: int | None
    checksum_sha256: str | None
    started_at: datetime
    finished_at: datetime | None
    error_message: str | None
    created_at: datetime


class FullExportPayload(BaseModel):
    format: str
    format_version: int
    app_version: str
    schema_revision: str
    exported_at: datetime
    tables: dict[str, list[dict[str, Any]]]
