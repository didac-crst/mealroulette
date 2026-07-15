from datetime import UTC, datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from mealroulette.models.household import DEFAULT_HOUSEHOLD_ID
from mealroulette.models.scheduler import SCHEDULER_SETTINGS_ID, SchedulerSettings
from mealroulette.services.household_time import household_local_today, household_timezone


def test_household_timezone_defaults_to_paris(db_session, scheduler_seed):
    zone = household_timezone(db_session, DEFAULT_HOUSEHOLD_ID)
    assert str(zone) == "Europe/Paris"


def test_household_timezone_uses_default_when_timezone_is_invalid(db_session, scheduler_seed):
    row = db_session.get(SchedulerSettings, SCHEDULER_SETTINGS_ID)
    assert row is not None
    row.timezone = "Not/A/Timezone"
    db_session.commit()

    zone = household_timezone(db_session, DEFAULT_HOUSEHOLD_ID)
    assert str(zone) == "UTC"


def test_household_local_today_uses_scheduler_timezone(db_session, scheduler_seed):
    row = db_session.get(SchedulerSettings, SCHEDULER_SETTINGS_ID)
    assert row is not None
    row.timezone = "Europe/Paris"
    db_session.commit()

    instant = datetime(2026, 7, 12, 22, 30, tzinfo=UTC)
    with patch("mealroulette.services.household_time.datetime") as mock_datetime:
        mock_datetime.now.return_value = instant
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        assert household_local_today(db_session, DEFAULT_HOUSEHOLD_ID) == instant.astimezone(
            ZoneInfo("Europe/Paris")
        ).date()
