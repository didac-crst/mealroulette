from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from mealroulette.models.scheduler import SchedulerSettings

DEFAULT_HOUSEHOLD_TIMEZONE = "Europe/Paris"


def household_timezone(db: Session, household_id: UUID) -> ZoneInfo:
    row = db.scalar(select(SchedulerSettings).where(SchedulerSettings.household_id == household_id))
    timezone_name = (
        row.timezone if row is not None and row.timezone else DEFAULT_HOUSEHOLD_TIMEZONE
    )
    try:
        return ZoneInfo(timezone_name)
    except Exception:
        return ZoneInfo("UTC")


def household_local_today(db: Session, household_id: UUID) -> date:
    return datetime.now(UTC).astimezone(household_timezone(db, household_id)).date()
