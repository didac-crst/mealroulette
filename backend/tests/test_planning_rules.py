from datetime import date, timedelta

import pytest

from mealroulette.models.enums import MealPlanItemStatus
from mealroulette.services.planning_rules import (
    LEFTOVER_SOURCE_WINDOW_DAYS,
    is_leftover_source_candidate,
    is_valid_leftover_source_status,
    is_within_leftover_window,
)

pytestmark = pytest.mark.unit


def test_valid_leftover_source_status_only_eaten():
    assert is_valid_leftover_source_status(MealPlanItemStatus.eaten) is True
    assert is_valid_leftover_source_status(MealPlanItemStatus.ate_leftovers) is False
    assert is_valid_leftover_source_status(MealPlanItemStatus.planned) is False
    assert is_valid_leftover_source_status(MealPlanItemStatus.skipped) is False


def test_within_leftover_window():
    item_date = date(2026, 7, 10)
    assert is_within_leftover_window(date(2026, 7, 10), item_date) is True
    assert is_within_leftover_window(date(2026, 7, 3), item_date) is True
    assert is_within_leftover_window(date(2026, 7, 2), item_date) is False
    assert is_within_leftover_window(date(2026, 7, 11), item_date) is False


def test_is_leftover_source_candidate():
    item_date = date(2026, 7, 10)
    assert is_leftover_source_candidate(
        source_id=1,
        source_date=date(2026, 7, 9),
        source_status=MealPlanItemStatus.eaten,
        item_id=2,
        item_date=item_date,
    )
    assert not is_leftover_source_candidate(
        source_id=1,
        source_date=date(2026, 7, 9),
        source_status=MealPlanItemStatus.ate_leftovers,
        item_id=2,
        item_date=item_date,
    )
    assert not is_leftover_source_candidate(
        source_id=2,
        source_date=date(2026, 7, 9),
        source_status=MealPlanItemStatus.eaten,
        item_id=2,
        item_date=item_date,
    )
    assert not is_leftover_source_candidate(
        source_id=1,
        source_date=item_date - timedelta(days=LEFTOVER_SOURCE_WINDOW_DAYS + 1),
        source_status=MealPlanItemStatus.eaten,
        item_id=2,
        item_date=item_date,
    )
