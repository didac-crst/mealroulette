from __future__ import annotations

import enum
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from fastapi import HTTPException, status
from sqlalchemy import func, inspect, select, text
from sqlalchemy.orm import Session

from mealroulette.core.config import settings
from mealroulette.models.backup import BACKUP_SETTINGS_ID, BackupRun, BackupSettings
from mealroulette.models.catalog import (
    Dish,
    DishSeasonality,
    DishTag,
    Ingredient,
    IngredientAlias,
    IngredientUnitConversion,
    Recipe,
    RecipeIngredient,
    RecipeStep,
    Tag,
    Unit,
)
from mealroulette.models.cooking import CookingTimerAlert
from mealroulette.models.enums import BackupRunStatus, BackupType
from mealroulette.models.user import UserRole
from mealroulette.models.planning import MealPlan, MealPlanItem, MealRating
from mealroulette.models.scheduler import PlanningRule, SchedulerSettings
from mealroulette.models.shopping import ShoppingList, ShoppingListItem
from mealroulette.models.taxonomy import FoodGroup, IngredientFamily
from mealroulette.models.telegram import TelegramSettings, TelegramSubscriber
from mealroulette.models.user import User
from mealroulette.schemas.backup import (
    BackupRunPublic,
    BackupSettingsPublic,
    BackupSettingsUpdateRequest,
    FullExportPayload,
)

EXPORT_FORMAT = "mealroulette.full_export"
EXPORT_FORMAT_VERSION = 1
CURRENT_SCHEMA_REVISION = "030_taxonomy_family_backfill"
APP_VERSION = "v0.8.0"
PG_DUMP_TIMEOUT_SECONDS = 3600
BACKUPS_ROOT = Path("/backups")

TABLE_SPECS: list[tuple[str, type]] = [
    ("users", User),
    ("units", Unit),
    ("food_groups", FoodGroup),
    ("ingredient_families", IngredientFamily),
    ("tags", Tag),
    ("ingredients", Ingredient),
    ("ingredient_aliases", IngredientAlias),
    ("ingredient_unit_conversions", IngredientUnitConversion),
    ("dishes", Dish),
    ("dish_tags", DishTag),
    ("dish_seasonality", DishSeasonality),
    ("recipes", Recipe),
    ("recipe_steps", RecipeStep),
    ("recipe_ingredients", RecipeIngredient),
    ("meal_plans", MealPlan),
    ("meal_plan_items", MealPlanItem),
    ("meal_reviews", MealRating),
    ("shopping_lists", ShoppingList),
    ("shopping_list_items", ShoppingListItem),
    ("telegram_settings", TelegramSettings),
    ("telegram_subscribers", TelegramSubscriber),
    ("planning_rules", PlanningRule),
    ("scheduler_settings", SchedulerSettings),
    ("cooking_timer_alerts", CookingTimerAlert),
    ("backup_settings", BackupSettings),
    ("backup_runs", BackupRun),
]

FK_CHECKS: dict[str, list[tuple[str, str, str]]] = {
    "ingredient_families": [("food_group_id", "food_groups", "id")],
    "ingredients": [("family_id", "ingredient_families", "id"), ("default_unit_id", "units", "id")],
    "ingredient_aliases": [("ingredient_id", "ingredients", "id")],
    "ingredient_unit_conversions": [("ingredient_id", "ingredients", "id"), ("unit_id", "units", "id")],
    "dishes": [],
    "dish_tags": [("dish_id", "dishes", "id"), ("tag_id", "tags", "id")],
    "dish_seasonality": [("dish_id", "dishes", "id")],
    "recipes": [("dish_id", "dishes", "id")],
    "recipe_steps": [("recipe_id", "recipes", "id")],
    "recipe_ingredients": [
        ("recipe_id", "recipes", "id"),
        ("ingredient_id", "ingredients", "id"),
        ("unit_id", "units", "id"),
    ],
    "meal_plan_items": [
        ("meal_plan_id", "meal_plans", "id"),
        ("dish_id", "dishes", "id"),
        ("recipe_id", "recipes", "id"),
        ("leftover_source_item_id", "meal_plan_items", "id"),
    ],
    "meal_reviews": [("meal_plan_item_id", "meal_plan_items", "id"), ("dish_id", "dishes", "id")],
    "shopping_list_items": [("shopping_list_id", "shopping_lists", "id"), ("ingredient_id", "ingredients", "id")],
    "cooking_timer_alerts": [
        ("user_id", "users", "id"),
        ("recipe_id", "recipes", "id"),
        ("recipe_step_id", "recipe_steps", "id"),
    ],
}


def serialize_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, enum.Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, time):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value


def serialize_row(instance: Any) -> dict[str, Any]:
    mapper = inspect(instance).mapper
    return {column.key: serialize_value(getattr(instance, column.key)) for column in mapper.columns}


def deserialize_row(model: type, row: dict[str, Any]) -> dict[str, Any]:
    mapper = inspect(model)
    result: dict[str, Any] = {}
    for column in mapper.columns:
        if column.name not in row:
            continue
        value = row[column.name]
        if value is None:
            result[column.name] = None
            continue
        enum_class = getattr(column.type, "enum_class", None)
        if enum_class is not None:
            result[column.name] = enum_class(value)
            continue
        python_type = column.type.python_type
        if python_type is datetime:
            result[column.name] = datetime.fromisoformat(value)
        elif python_type is date:
            result[column.name] = date.fromisoformat(value)
        elif python_type is time:
            result[column.name] = time.fromisoformat(value)
        elif python_type is Decimal:
            result[column.name] = Decimal(str(value))
        else:
            result[column.name] = value
    return result


class BackupService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_settings_row(self) -> BackupSettings:
        row = self.db.get(BackupSettings, BACKUP_SETTINGS_ID)
        if row is None:
            row = BackupSettings(id=BACKUP_SETTINGS_ID)
            self.db.add(row)
            self.db.commit()
            self.db.refresh(row)
        return row

    def get_settings_public(self) -> BackupSettingsPublic:
        return self._settings_to_public(self.get_settings_row())

    def update_settings(self, payload: BackupSettingsUpdateRequest) -> BackupSettingsPublic:
        row = self.get_settings_row()
        updates = payload.model_dump(exclude_unset=True)
        for field, value in updates.items():
            setattr(row, field, value)
        self._validate_backup_path(row.backup_path)
        self.db.commit()
        self.db.refresh(row)
        return self._settings_to_public(row)

    def list_runs(self, *, limit: int = 50) -> list[BackupRunPublic]:
        rows = self.db.scalars(
            select(BackupRun).order_by(BackupRun.started_at.desc(), BackupRun.id.desc()).limit(limit)
        ).all()
        return [self._run_to_public(row) for row in rows]

    def build_full_export(self) -> FullExportPayload:
        tables: dict[str, list[dict[str, Any]]] = {}
        for table_name, model in TABLE_SPECS:
            rows = self.db.scalars(select(model)).all()
            if table_name == "backup_runs":
                rows = [
                    row
                    for row in rows
                    if row.status != BackupRunStatus.running and row.file_path is not None
                ]
            pk_cols = [column.name for column in inspect(model).primary_key]
            rows.sort(key=lambda row: tuple(getattr(row, key) for key in pk_cols))
            tables[table_name] = [serialize_row(row) for row in rows]
        return FullExportPayload(
            format=EXPORT_FORMAT,
            format_version=EXPORT_FORMAT_VERSION,
            app_version=APP_VERSION,
            schema_revision=CURRENT_SCHEMA_REVISION,
            exported_at=datetime.now().astimezone(),
            tables=tables,
        )

    def export_full_json(self) -> str:
        return json.dumps(self.build_full_export().model_dump(mode="json"), indent=2, sort_keys=True)

    def validate_import_payload(self, payload: dict[str, Any]) -> FullExportPayload:
        if payload.get("format") != EXPORT_FORMAT:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Unsupported export format")
        if payload.get("format_version") != EXPORT_FORMAT_VERSION:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Unsupported format version")
        if payload.get("schema_revision") != CURRENT_SCHEMA_REVISION:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Incompatible schema revision: {payload.get('schema_revision')}",
            )
        try:
            export = FullExportPayload.model_validate(payload)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc
        self._validate_table_shapes(export)
        self._validate_foreign_keys(export)
        self._validate_admin_user(export)
        return export

    def import_full_export(self, payload: dict[str, Any]) -> None:
        export = self.validate_import_payload(payload)
        if not self._database_is_empty_for_import():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Import requires an empty database",
            )
        try:
            for table_name, model in TABLE_SPECS:
                rows = export.tables.get(table_name, [])
                for row in rows:
                    data = deserialize_row(model, row)
                    self.db.add(model(**data))
                self.db.flush()
            self._reset_sequences()
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def run_manual_backup(self) -> list[BackupRunPublic]:
        settings_row = self.get_settings_row()
        results: list[BackupRunPublic] = []
        if settings_row.include_json_export:
            results.append(self._run_json_export(settings_row))
        if settings_row.include_pg_dump:
            results.append(self._run_pg_dump(settings_row))
        if not results:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No backup types enabled")
        settings_row.last_backup_at = datetime.now().astimezone()
        settings_row.last_error = None
        self.db.commit()
        return results

    def run_scheduled_backup(self) -> list[BackupRunPublic] | None:
        settings_row = self.get_settings_row()
        if not settings_row.enabled:
            return None
        from zoneinfo import ZoneInfo

        tz = ZoneInfo(settings_row.timezone)
        now_local = datetime.now(tz)
        if now_local.hour != settings_row.run_time.hour or now_local.minute != settings_row.run_time.minute:
            return None
        if settings_row.last_backup_at is not None:
            last_local = settings_row.last_backup_at.astimezone(tz)
            if last_local.date() == now_local.date():
                return None
        try:
            results = self.run_manual_backup()
            self.cleanup_retention(settings_row)
            return results
        except Exception as exc:
            settings_row.last_error = str(exc)
            self.db.commit()
            raise

    def cleanup_retention(self, settings_row: BackupSettings | None = None) -> int:
        row = settings_row or self.get_settings_row()
        backup_dir = self._resolve_backup_dir(row.backup_path)
        if not backup_dir.exists():
            return 0
        cutoff = datetime.now().astimezone().timestamp() - (row.retention_days * 86400)
        deleted = 0
        pattern = re.compile(r"^mealroulette-(full|pg)-\d{8}-\d{6}Z\.(json|dump)$")
        for path in backup_dir.iterdir():
            if not path.is_file() or not pattern.match(path.name):
                continue
            if path.stat().st_mtime < cutoff:
                path.unlink(missing_ok=True)
                deleted += 1
        return deleted

    def _run_json_export(self, settings_row: BackupSettings) -> BackupRunPublic:
        backup_dir = self._resolve_backup_dir(settings_row.backup_path)
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%SZ")
        final_name = f"mealroulette-full-{timestamp}.json"
        final_path = backup_dir / final_name
        content = self.export_full_json().encode("utf-8")

        run = BackupRun(backup_type=BackupType.json_export, status=BackupRunStatus.running)
        self.db.add(run)
        self.db.flush()
        try:
            with tempfile.NamedTemporaryFile(dir=backup_dir, delete=False) as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
                temp_path = Path(handle.name)
            checksum = hashlib.sha256(content).hexdigest()
            temp_path.replace(final_path)
            run.status = BackupRunStatus.succeeded
            run.file_path = final_name
            run.file_size_bytes = len(content)
            run.checksum_sha256 = checksum
            run.finished_at = datetime.now().astimezone()
        except Exception as exc:
            run.status = BackupRunStatus.failed
            run.error_message = str(exc)
            run.finished_at = datetime.now().astimezone()
            settings_row.last_error = str(exc)
            raise
        finally:
            self.db.commit()
            self.db.refresh(run)
        return self._run_to_public(run)

    def _run_pg_dump(self, settings_row: BackupSettings) -> BackupRunPublic:
        run = BackupRun(backup_type=BackupType.pg_dump, status=BackupRunStatus.running)
        self.db.add(run)
        self.db.flush()
        try:
            backup_dir = self._resolve_backup_dir(settings_row.backup_path)
            backup_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%SZ")
            final_name = f"mealroulette-pg-{timestamp}.dump"
            final_path = backup_dir / final_name
            temp_path = final_path.with_suffix(".dump.tmp")
            self._execute_pg_dump(temp_path)
            checksum = hashlib.sha256(temp_path.read_bytes()).hexdigest()
            temp_path.replace(final_path)
            run.status = BackupRunStatus.succeeded
            run.file_path = final_name
            run.file_size_bytes = final_path.stat().st_size
            run.checksum_sha256 = checksum
            run.finished_at = datetime.now().astimezone()
        except Exception as exc:
            run.status = BackupRunStatus.failed
            run.error_message = str(exc)
            run.finished_at = datetime.now().astimezone()
            settings_row.last_error = str(exc)
            raise
        finally:
            self.db.commit()
            self.db.refresh(run)
        return self._run_to_public(run)

    def _execute_pg_dump(self, output_path: Path) -> None:
        if shutil.which("pg_dump") is None:
            raise RuntimeError("pg_dump is not available")
        parsed = urlparse(settings.database_url.replace("+psycopg", ""))
        env = os.environ.copy()
        if parsed.password:
            env["PGPASSWORD"] = parsed.password
        command = [
            "pg_dump",
            "--format=custom",
            "--file",
            str(output_path),
            "--host",
            parsed.hostname or "localhost",
            "--port",
            str(parsed.port or 5432),
            "--username",
            parsed.username or "mealroulette",
            parsed.path.lstrip("/"),
        ]
        subprocess.run(command, check=True, env=env, capture_output=True, text=True, timeout=PG_DUMP_TIMEOUT_SECONDS)

    def _validate_table_shapes(self, export: FullExportPayload) -> None:
        for table_name, _model in TABLE_SPECS:
            rows = export.tables.get(table_name)
            if rows is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=f"Missing table array: {table_name}",
                )
            if not isinstance(rows, list):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=f"Table {table_name} must be an array",
                )
        for table_name, rows in export.tables.items():
            seen: set[Any] = set()
            model = dict(TABLE_SPECS).get(table_name)
            if model is None:
                continue
            pk_cols = [column.name for column in inspect(model).primary_key]
            for row in rows:
                if not isinstance(row, dict):
                    raise HTTPException(status_code=422, detail=f"Invalid row in {table_name}")
                key = tuple(row.get(col) for col in pk_cols)
                if key in seen:
                    raise HTTPException(status_code=422, detail=f"Duplicate primary key in {table_name}: {key}")
                seen.add(key)

    def _validate_foreign_keys(self, export: FullExportPayload) -> None:
        id_maps: dict[str, set[Any]] = {}
        for table_name, model in TABLE_SPECS:
            rows = export.tables.get(table_name, [])
            pk_cols = [column.name for column in inspect(model).primary_key]
            if len(pk_cols) == 1:
                id_maps[table_name] = {row.get(pk_cols[0]) for row in rows}
            else:
                id_maps[table_name] = {tuple(row.get(col) for col in pk_cols) for row in rows}

        for table_name, checks in FK_CHECKS.items():
            rows = export.tables.get(table_name, [])
            for row in rows:
                for field, target_table, target_col in checks:
                    value = row.get(field)
                    if value is None:
                        continue
                    target_ids = id_maps.get(target_table, set())
                    if target_col == "id" and len(inspect(dict(TABLE_SPECS)[target_table]).primary_key) == 1:
                        if value not in target_ids:
                            raise HTTPException(
                                status_code=422,
                                detail=f"Unresolved FK {table_name}.{field} -> {target_table}.{target_col} ({value})",
                            )
                    elif (value,) not in target_ids and value not in target_ids:
                        raise HTTPException(
                            status_code=422,
                            detail=f"Unresolved FK {table_name}.{field} -> {target_table} ({value})",
                        )

    def _validate_admin_user(self, export: FullExportPayload) -> None:
        users = export.tables.get("users", [])
        if not any(user.get("role") == UserRole.admin.value for user in users):
            raise HTTPException(status_code=422, detail="Export must include at least one admin user")

    def _database_is_empty_for_import(self) -> bool:
        counts = [
            self.db.scalar(select(func.count()).select_from(User)) or 0,
            self.db.scalar(select(func.count()).select_from(Ingredient)) or 0,
            self.db.scalar(select(func.count()).select_from(Dish)) or 0,
            self.db.scalar(select(func.count()).select_from(MealPlan)) or 0,
        ]
        return all(count == 0 for count in counts)

    def _reset_sequences(self) -> None:
        for table_name, model in TABLE_SPECS:
            pk_cols = [column.name for column in inspect(model).primary_key]
            if len(pk_cols) != 1 or pk_cols[0] != "id":
                continue
            self.db.execute(
                text(
                    f"SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), "
                    f"COALESCE((SELECT MAX(id) FROM {table_name}), 1), true)"
                )
            )

    @staticmethod
    def _resolve_backup_dir(backup_path: str) -> Path:
        path = Path(backup_path)
        if not path.is_absolute():
            path = BACKUPS_ROOT / path
        return path.resolve()

    @staticmethod
    def _validate_backup_path(backup_path: str) -> None:
        resolved = BackupService._resolve_backup_dir(backup_path)
        root = BACKUPS_ROOT.resolve()
        if resolved != root and root not in resolved.parents:
            raise HTTPException(status_code=422, detail="backup_path must stay under /backups")

    @staticmethod
    def _settings_to_public(row: BackupSettings) -> BackupSettingsPublic:
        return BackupSettingsPublic(
            enabled=row.enabled,
            run_time=row.run_time.isoformat(),
            timezone=row.timezone,
            retention_days=row.retention_days,
            backup_path=row.backup_path,
            include_json_export=row.include_json_export,
            include_pg_dump=row.include_pg_dump,
            last_backup_at=row.last_backup_at,
            last_error=row.last_error,
        )

    @staticmethod
    def _run_to_public(row: BackupRun) -> BackupRunPublic:
        return BackupRunPublic(
            id=row.id,
            backup_type=row.backup_type.value,
            status=row.status.value,
            file_path=row.file_path,
            file_size_bytes=row.file_size_bytes,
            checksum_sha256=row.checksum_sha256,
            started_at=row.started_at,
            finished_at=row.finished_at,
            error_message=row.error_message,
            created_at=row.created_at,
        )
