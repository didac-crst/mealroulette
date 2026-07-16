"""Verify migration 033 remaps legacy integer user IDs to UUID tenancy tables."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import psycopg
import pytest
from alembic import command
from alembic.config import Config
from psycopg import sql
from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url

from mealroulette.models.household import DEFAULT_HOUSEHOLD_ID

from mealroulette.core.config import Settings, get_settings
import mealroulette.core.config as config_module

pytestmark = pytest.mark.integration

LEGACY_ADMIN_ID = 1
LEGACY_MEMBER_ID = 2
STUB_DISH_ID = 9001
STUB_RECIPE_ID = 9001
STUB_STEP_ID = 9001


def _migration_database_url() -> str:
    worker = os.environ.get("PYTEST_XDIST_WORKER")
    database_name = (
        "mealroulette_test_migration"
        if worker in (None, "master")
        else f"mealroulette_test_migration_{worker}"
    )
    base_url = os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql+psycopg://mealroulette:mealroulette@localhost:5432/mealroulette_test",
    )
    return make_url(base_url).set(database=database_name).render_as_string(hide_password=False)


def _alembic_config(database_url: str) -> Config:
    backend_dir = Path(__file__).resolve().parents[1]
    config = Config(str(backend_dir / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def _ensure_migration_database(database_url: str) -> None:
    url = make_url(database_url)
    admin_url = os.environ.get(
        "ADMIN_DATABASE_URL",
        "postgresql://mealroulette:mealroulette@localhost:5432/mealroulette",
    )
    with psycopg.connect(admin_url, autocommit=True) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (url.database,))
            if cursor.fetchone() is None:
                cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(url.database)))


def _reset_database(engine) -> None:
    with engine.connect() as connection:
        connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
        connection.commit()


def _seed_revision_032_data(connection) -> None:
    connection.execute(
        text(
            """
            INSERT INTO users (id, username, email, password_hash, role, active)
            VALUES
                (:admin_id, 'legacy-admin', 'legacy-admin@example.com', 'hash', 'admin', true),
                (:member_id, 'legacy-member', 'legacy-member@example.com', 'hash', 'user', true)
            """
        ),
        {"admin_id": LEGACY_ADMIN_ID, "member_id": LEGACY_MEMBER_ID},
    )
    expires_at = datetime.now(UTC) + timedelta(days=1)
    connection.execute(
        text(
            """
            INSERT INTO refresh_tokens (user_id, token_jti, expires_at)
            VALUES
                (:admin_id, 'legacy-admin-jti', :expires_at),
                (:member_id, 'legacy-member-jti', :expires_at)
            """
        ),
        {"admin_id": LEGACY_ADMIN_ID, "member_id": LEGACY_MEMBER_ID, "expires_at": expires_at},
    )
    connection.execute(
        text(
            """
            INSERT INTO dishes (id, public_key, name, active, meal_composition, status)
            VALUES (:dish_id, 'migrate033dish', 'Migration Test Dish', true, 'main_dish', 'active')
            """
        ),
        {"dish_id": STUB_DISH_ID},
    )
    connection.execute(
        text(
            """
            INSERT INTO recipes (
                id, dish_id, public_key, sequence_number, variant_name, recipe_type, is_main, is_thermomix
            )
            VALUES (
                :recipe_id, :dish_id, 'migrate033recipe', 1, 'default', 'standard', false, false
            )
            """
        ),
        {"recipe_id": STUB_RECIPE_ID, "dish_id": STUB_DISH_ID},
    )
    connection.execute(
        text(
            """
            INSERT INTO recipe_steps (id, recipe_id, step_number, instruction, is_thermomix_step)
            VALUES (:step_id, :recipe_id, 1, 'Migration test step', false)
            """
        ),
        {"step_id": STUB_STEP_ID, "recipe_id": STUB_RECIPE_ID},
    )
    fire_at = datetime.now(UTC) + timedelta(hours=1)
    connection.execute(
        text(
            """
            INSERT INTO cooking_timer_alerts (
                user_id, recipe_id, recipe_step_id, step_number, dish_name, recipe_name, fire_at, status
            )
            VALUES (
                :admin_id, :recipe_id, :step_id, 1, 'Migration Test Dish', 'default', :fire_at, 'pending'
            )
            """
        ),
        {
            "admin_id": LEGACY_ADMIN_ID,
            "recipe_id": STUB_RECIPE_ID,
            "step_id": STUB_STEP_ID,
            "fire_at": fire_at,
        },
    )


def _configure_migration_settings(database_url: str) -> None:
    os.environ["DATABASE_URL"] = database_url
    os.environ["TEST_DATABASE_URL"] = database_url
    migration_settings = Settings(
        database_url=database_url,
        test_database_url=database_url,
        secret_key="test-secret-key-for-hs256-at-least-32-bytes",
    )
    config_module.settings = migration_settings
    get_settings.cache_clear()


def test_migration_033_remaps_legacy_users_and_tenancy():
    database_url = _migration_database_url()
    _ensure_migration_database(database_url)
    _configure_migration_settings(database_url)
    engine = create_engine(database_url, pool_pre_ping=True)

    try:
        _reset_database(engine)
        alembic_config = _alembic_config(database_url)
        command.upgrade(alembic_config, "032_reroll_history")

        with engine.begin() as connection:
            _seed_revision_032_data(connection)

        command.upgrade(alembic_config, "033_household_tenancy_identity")

        with engine.connect() as connection:
            admin_uuid = connection.execute(
                text("SELECT id FROM users WHERE username = 'legacy-admin'")
            ).scalar_one()
            member_uuid = connection.execute(
                text("SELECT id FROM users WHERE username = 'legacy-member'")
            ).scalar_one()

            assert isinstance(admin_uuid, UUID)
            assert isinstance(member_uuid, UUID)
            assert admin_uuid != member_uuid

            admin_refresh_user_id = connection.execute(
                text("SELECT user_id FROM refresh_tokens WHERE token_jti = 'legacy-admin-jti'")
            ).scalar_one()
            member_refresh_user_id = connection.execute(
                text("SELECT user_id FROM refresh_tokens WHERE token_jti = 'legacy-member-jti'")
            ).scalar_one()
            assert admin_refresh_user_id == admin_uuid
            assert member_refresh_user_id == member_uuid

            alert_user_id = connection.execute(
                text(
                    """
                    SELECT user_id FROM cooking_timer_alerts
                    WHERE dish_name = 'Migration Test Dish'
                    """
                )
            ).scalar_one()
            assert alert_user_id == admin_uuid

            default_household = connection.execute(
                text("SELECT id, name FROM households WHERE id = :household_id"),
                {"household_id": DEFAULT_HOUSEHOLD_ID},
            ).one()
            assert default_household.name == "Default household"

            admin_membership = connection.execute(
                text(
                    """
                    SELECT role FROM household_memberships
                    WHERE user_id = :user_id AND household_id = :household_id
                    """
                ),
                {"user_id": admin_uuid, "household_id": DEFAULT_HOUSEHOLD_ID},
            ).scalar_one()
            member_membership = connection.execute(
                text(
                    """
                    SELECT role FROM household_memberships
                    WHERE user_id = :user_id AND household_id = :household_id
                    """
                ),
                {"user_id": member_uuid, "household_id": DEFAULT_HOUSEHOLD_ID},
            ).scalar_one()
            assert admin_membership == "household_admin"
            assert member_membership == "household_member"

            admin_platform_roles = connection.execute(
                text("SELECT role FROM user_platform_roles WHERE user_id = :user_id"),
                {"user_id": admin_uuid},
            ).scalars().all()
            member_platform_roles = connection.execute(
                text("SELECT role FROM user_platform_roles WHERE user_id = :user_id"),
                {"user_id": member_uuid},
            ).scalars().all()
            assert admin_platform_roles == ["platform_admin"]
            assert member_platform_roles == []

            migration_table_exists = connection.execute(
                text(
                    """
                    SELECT EXISTS (
                        SELECT 1
                        FROM information_schema.tables
                        WHERE table_schema = 'public' AND table_name = '_user_id_migration'
                    )
                    """
                )
            ).scalar_one()
            assert migration_table_exists is False
    finally:
        get_settings.cache_clear()
        engine.dispose()
