from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from mealroulette.worker import run_scheduled_roulette


@pytest.mark.integration
def test_run_scheduled_roulette_continues_after_household_failure():
    first = MagicMock(household_id=uuid4())
    second = MagicMock(household_id=uuid4())
    ok_result = MagicMock(assignments_count=2, week_start_date="2026-07-06")
    services: dict = {}

    with (
        patch("mealroulette.worker._session_factory") as session_factory,
        patch("mealroulette.services.scheduler_settings.SchedulerSettingsService") as settings_cls,
        patch("mealroulette.worker.ScheduledRouletteService") as roulette_cls,
    ):
        session_factory.return_value.__enter__.return_value = MagicMock()
        settings_cls.return_value.list_all_rows.return_value = [first, second]

        def factory(_db, household_id=None, **_kwargs):
            service = MagicMock()
            services[household_id] = service
            if household_id == first.household_id:
                service.run_scheduled.side_effect = RuntimeError("boom")
            else:
                service.run_scheduled.return_value = ok_result
            return service

        roulette_cls.side_effect = factory
        run_scheduled_roulette()

    assert roulette_cls.call_count == 2
    services[first.household_id].run_scheduled.assert_called_once_with()
    services[second.household_id].run_scheduled.assert_called_once_with()
