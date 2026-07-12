from __future__ import annotations

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from mealroulette.models.scheduler import SCHEDULER_SETTINGS_ID, SchedulerSettings

DEFAULT_HOUSEHOLD_TIMEZONE = "Europe/Paris"


def household_timezone(db: Session) -> ZoneInfo:
    row = db.get(SchedulerSettings, SCHEDULER_SETTINGS_ID)
    timezone_name = row.timezone if row is not None else DEFAULT_HOUSEHOLD_TIMEZONE
    try:
        return ZoneInfo(timezone_name)
    except Exception:
        return ZoneInfo("UTC")


def household_local_today(db: Session) -> date:
    return datetime.now(UTC).astimezone(household_timezone(db)).date()
