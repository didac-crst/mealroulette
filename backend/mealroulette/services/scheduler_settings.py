from __future__ import annotations

from datetime import UTC, datetime, time
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from mealroulette.models.scheduler import SchedulerSettings
from mealroulette.schemas.scheduler import SchedulerSettingsPublic, SchedulerSettingsUpdateRequest


class SchedulerSettingsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_all_rows(self) -> list[SchedulerSettings]:
        return list(self.db.scalars(select(SchedulerSettings).order_by(SchedulerSettings.id)))

    def get_row(self, household_id: UUID) -> SchedulerSettings:
        row = self.db.scalar(
            select(SchedulerSettings).where(SchedulerSettings.household_id == household_id)
        )
        if row is None:
            row = SchedulerSettings(household_id=household_id)
            self.db.add(row)
            try:
                self.db.commit()
            except IntegrityError:
                self.db.rollback()
                row = self.db.scalar(
                    select(SchedulerSettings).where(SchedulerSettings.household_id == household_id)
                )
                if row is None:
                    raise
            else:
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

    def get_public(self, household_id: UUID) -> SchedulerSettingsPublic:
        return self.to_public(self.get_row(household_id))

    def update(self, household_id: UUID, payload: SchedulerSettingsUpdateRequest) -> SchedulerSettingsPublic:
        row = self.get_row(household_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(row, field, value)
        self.db.commit()
        self.db.refresh(row)
        return self.to_public(row)

    def record_roulette_success(self, row: SchedulerSettings) -> None:
        row.last_roulette_at = datetime.now(UTC)
        row.last_error = None
        self.db.commit()

    def record_roulette_failure(self, error: str, row: SchedulerSettings) -> None:
        row.last_error = error[:2000]
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
        scheduled_minutes = scheduled.hour * 60 + scheduled.minute
        local_minutes = local.hour * 60 + local.minute
        if local_minutes < scheduled_minutes:
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
