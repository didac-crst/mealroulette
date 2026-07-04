from __future__ import annotations

from datetime import UTC, datetime, time
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from mealroulette.models.scheduler import SCHEDULER_SETTINGS_ID, SchedulerSettings
from mealroulette.schemas.scheduler import SchedulerSettingsPublic, SchedulerSettingsUpdateRequest


class SchedulerSettingsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_row(self) -> SchedulerSettings:
        row = self.db.get(SchedulerSettings, SCHEDULER_SETTINGS_ID)
        if row is None:
            row = SchedulerSettings(id=SCHEDULER_SETTINGS_ID)
            self.db.add(row)
            self.db.commit()
            self.db.refresh(row)
        return row

    @staticmethod
    def to_public(row: SchedulerSettings) -> SchedulerSettingsPublic:
        return SchedulerSettingsPublic(
            enabled=row.enabled,
            run_weekday=row.run_weekday,
            run_time=row.run_time,
            timezone=row.timezone,
            target_week_offset=row.target_week_offset,
            notify_telegram=row.notify_telegram,
            notify_planning_days=row.notify_planning_days,
            last_roulette_at=row.last_roulette_at,
            last_error=row.last_error,
        )

    def get_public(self) -> SchedulerSettingsPublic:
        return self.to_public(self.get_row())

    def update(self, payload: SchedulerSettingsUpdateRequest) -> SchedulerSettingsPublic:
        row = self.get_row()
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(row, field, value)
        self.db.commit()
        self.db.refresh(row)
        return self.to_public(row)

    def record_roulette_success(self, row: SchedulerSettings | None = None) -> None:
        settings_row = row or self.get_row()
        settings_row.last_roulette_at = datetime.now(UTC)
        settings_row.last_error = None
        self.db.commit()

    def record_roulette_failure(self, error: str, row: SchedulerSettings | None = None) -> None:
        settings_row = row or self.get_row()
        settings_row.last_error = error[:2000]
        self.db.commit()

    @staticmethod
    def should_run_scheduled(
        row: SchedulerSettings,
        *,
        now: datetime | None = None,
    ) -> bool:
        if not row.enabled:
            return False
        current = now or datetime.now(UTC)
        try:
            zone = ZoneInfo(row.timezone)
        except Exception:
            zone = ZoneInfo("UTC")
        local = current.astimezone(zone)
        scheduled = row.run_time
        if local.weekday() != row.run_weekday:
            return False
        if (local.hour, local.minute) != (scheduled.hour, scheduled.minute):
            return False
        if row.last_roulette_at is not None:
            last_local = row.last_roulette_at.astimezone(zone)
            if last_local.date() == local.date():
                return False
        return True

    @staticmethod
    def weekday_label(weekday: int) -> str:
        labels = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
        return labels[weekday]
