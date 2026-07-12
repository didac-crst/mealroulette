from datetime import UTC, datetime, time

import pytest

from mealroulette.models.scheduler import SCHEDULER_SETTINGS_ID, SchedulerSettings
from mealroulette.schemas.scheduler import SchedulerSettingsUpdateRequest
from mealroulette.services.scheduler_settings import SchedulerSettingsService


@pytest.mark.integration
def test_scheduler_settings_defaults(db_session):
    public = SchedulerSettingsService(db_session).get_public()

    assert public.enabled is False
    assert public.run_weekday == 4
    assert public.run_time == time(18, 0)
    assert public.target_week_offset == 1
    assert public.notify_telegram is True
    assert public.notify_planning_days == 7


@pytest.mark.integration
def test_scheduler_settings_update(db_session):
    public = SchedulerSettingsService(db_session).update(
        SchedulerSettingsUpdateRequest(
            enabled=True,
            run_weekday=4,
            run_time=time(9, 30),
            target_week_offset=1,
            notify_planning_days=5,
        )
    )

    assert public.enabled is True
    assert public.run_time == time(9, 30)
    assert public.notify_planning_days == 5


@pytest.mark.integration
def test_should_run_scheduled_once_per_local_day(db_session):
    service = SchedulerSettingsService(db_session)
    row = service.get_row()
    row.enabled = True
    row.run_weekday = 4
    row.run_time = time(18, 0)
    row.timezone = "UTC"
    db_session.commit()

    friday_1800 = datetime(2026, 7, 3, 18, 0, tzinfo=UTC)
    assert service.should_run_scheduled(row, now=friday_1800) is True

    row.last_roulette_at = friday_1800
    assert service.should_run_scheduled(row, now=friday_1800) is False

    saturday_1800 = datetime(2026, 7, 4, 18, 0, tzinfo=UTC)
    assert service.should_run_scheduled(row, now=saturday_1800) is False


@pytest.mark.integration
def test_should_run_scheduled_after_run_time_same_day(db_session):
    service = SchedulerSettingsService(db_session)
    row = service.get_row()
    row.enabled = True
    row.run_weekday = 4
    row.run_time = time(18, 0)
    row.timezone = "UTC"
    row.last_roulette_at = None
    db_session.commit()

    friday_1830 = datetime(2026, 7, 3, 18, 30, tzinfo=UTC)
    assert service.should_run_scheduled(row, now=friday_1830) is True

    friday_1759 = datetime(2026, 7, 3, 17, 59, tzinfo=UTC)
    assert service.should_run_scheduled(row, now=friday_1759) is False


@pytest.mark.integration
def test_record_roulette_success_clears_error(db_session):
    service = SchedulerSettingsService(db_session)
    row = service.get_row()
    row.last_error = "previous failure"
    db_session.commit()

    service.record_roulette_success(row)

    refreshed = db_session.get(SchedulerSettings, SCHEDULER_SETTINGS_ID)
    assert refreshed is not None
    assert refreshed.last_error is None
    assert refreshed.last_roulette_at is not None
