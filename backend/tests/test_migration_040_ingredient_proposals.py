"""Safety checks for migration 040 ingredient_proposals shape detection."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

MIGRATION_PATH = (
    Path(__file__).resolve().parents[1] / "alembic" / "versions" / "040_ingredient_proposals.py"
)


def _load_migration():
    spec = importlib.util.spec_from_file_location("migration_040_ingredient_proposals", MIGRATION_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.unit
def test_phase_16c_shape_requires_core_columns():
    migration = _load_migration()
    assert migration._is_phase_16c_shape(
        {
            "normalized_name",
            "resolution_status",
            "proposed_name",
            "source_locale",
            "proposed_by_user_id",
            "id",
        }
    )
    assert not migration._is_phase_16c_shape({"proposed_name", "status"})


@pytest.mark.unit
def test_legacy_umbrella_shape_uses_status_enum_marker():
    migration = _load_migration()

    class _Result:
        def scalar(self):
            return 1

    bind = SimpleNamespace(execute=lambda *_args, **_kwargs: _Result())
    assert migration._is_known_legacy_umbrella_shape(
        bind,
        {"id", "proposed_name", "status"},
    )


@pytest.mark.unit
def test_unknown_shape_is_neither_phase16c_nor_legacy():
    migration = _load_migration()

    class _Result:
        def scalar(self):
            return None

    bind = SimpleNamespace(execute=lambda *_args, **_kwargs: _Result())
    columns = {"id", "foo", "bar"}
    assert not migration._is_phase_16c_shape(columns)
    assert not migration._is_known_legacy_umbrella_shape(bind, columns)
