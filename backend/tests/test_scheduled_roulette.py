from datetime import UTC, date, datetime, time
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from mealroulette.data.import_dishes import DEFAULT_FIXTURE_PATH, import_dish_fixtures
from mealroulette.models.household import DEFAULT_HOUSEHOLD_ID
from mealroulette.models.scheduler import SCHEDULER_SETTINGS_ID, SchedulerSettings
from mealroulette.services.planning import PlanningService
from mealroulette.services.scheduled_roulette import ScheduledRouletteService
from mealroulette.services.scheduler_settings import SchedulerSettingsService

pytestmark = pytest.mark.integration


def _seed(db_session):
    import_dish_fixtures(db_session, DEFAULT_FIXTURE_PATH)


def test_target_week_start_offsets_from_reference_monday():
    reference = date(2026, 7, 8)  # Wednesday
    assert ScheduledRouletteService.target_week_start(reference, 0) == date(2026, 7, 6)
    assert ScheduledRouletteService.target_week_start(reference, 1) == date(2026, 7, 13)


def test_run_scheduled_skips_when_disabled(db_session, catalog_seed, scheduler_seed):
    service = ScheduledRouletteService(db_session)
    row = service.settings_service.get_row(DEFAULT_HOUSEHOLD_ID)
    row.enabled = False
    db_session.commit()

    friday_1800 = datetime(2026, 7, 3, 18, 0, tzinfo=UTC)
    assert service.run_scheduled(now=friday_1800) is None


def test_run_now_generates_next_week(db_session, catalog_seed, scheduler_seed):
    _seed(db_session)
    service = ScheduledRouletteService(db_session)
    row = service.settings_service.get_row(DEFAULT_HOUSEHOLD_ID)
    row.enabled = True
    row.target_week_offset = 1
    db_session.commit()

    reference_today = date(2026, 7, 1)
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            "mealroulette.services.scheduled_roulette.local_today",
            lambda _settings: reference_today,
        )
        result = service.run_now()

    assert result.assignments_count == 14
    assert result.week_start_date == date(2026, 7, 6)

    refreshed = db_session.get(SchedulerSettings, SCHEDULER_SETTINGS_ID)
    assert refreshed is not None
    assert refreshed.last_roulette_at is not None
    assert refreshed.last_error is None


def test_run_now_records_failure_when_no_dishes(db_session, catalog_seed, scheduler_seed):
    service = ScheduledRouletteService(db_session)
    reference_today = date(2026, 7, 1)
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            "mealroulette.services.scheduled_roulette.local_today",
            lambda _settings: reference_today,
        )
        with pytest.raises(HTTPException):
            service.run_now()

    refreshed = db_session.get(SchedulerSettings, SCHEDULER_SETTINGS_ID)
    assert refreshed is not None
    assert refreshed.last_error is not None


def test_notify_telegram_sends_new_roulette_heading(db_session, catalog_seed, scheduler_seed, monkeypatch):
    _seed(db_session)
    mock_client = MagicMock()
    service = ScheduledRouletteService(db_session, client=mock_client)
    row = service.settings_service.get_row(DEFAULT_HOUSEHOLD_ID)
    row.notify_telegram = True
    row.notify_planning_days = 7
    db_session.commit()

    from mealroulette.models.telegram import TelegramSubscriber
    from mealroulette.services.telegram_settings import TelegramSettingsService

    db_session.add(TelegramSubscriber(chat_id="12345", telegram_user_id="99", username="tester"))
    db_session.commit()

    reference_today = date(2026, 7, 1)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:TEST-BOT-TOKEN")
    monkeypatch.setattr(
        "mealroulette.services.scheduled_roulette.local_today",
        lambda _settings: reference_today,
    )
    monkeypatch.setattr(
        "mealroulette.services.scheduled_roulette.TelegramSettingsService.bot_token_configured",
        lambda: True,
    )
    monkeypatch.setattr(
        "mealroulette.services.scheduled_roulette.get_settings",
        lambda: type("S", (), {"telegram_bot_token": "123456:TEST-BOT-TOKEN"})(),
    )

    result = service.run_now()
    assert result.telegram is not None
    assert result.telegram.sent is True
    assert mock_client.send_message.called
    message = mock_client.send_message.call_args[0][2]
    assert "<b>New roulette</b>" in message


def test_run_roulette_api(client, catalog_seed, scheduler_seed, admin_headers, db_session):
    _seed(db_session)
    response = client.post("/api/scheduler/run-roulette", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["ran"] is True
    assert body["assignments_count"] == 14
    assert body["week_start_date"] is not None
