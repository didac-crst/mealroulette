# Backup, Export, and Import

Architecture specification for **Phase 11 / v1.0**. This document refines the high-level backup requirements in [SPECS.md](../SPECS.md#310-backup-export-and-import) and the Phase 11 roadmap entry in [CURSOR_ROADMAP.md](CURSOR_ROADMAP.md#phase-11---taxonomy-hardening--backup-export-and-import).

## Prerequisites (taxonomy hardening)

**Do not finalize the export schema until taxonomy hardening is complete.**

Per [ADR 002](adr/002-canonical-taxonomy-before-backup.md) and [PHASE11_HANDOFF.md](PHASE11_HANDOFF.md), the backup format must reflect:

- first-class `food_groups` and `ingredient_families` tables (not string fields on `ingredients` alone);
- canonical ingredient references on recipe ingredients;
- scheduler weekly targets driven by computed traits where derivable, with explicit curated fields for non-derivable classifications (e.g. `soup`);
- a clear decision on legacy `tags` / `dish_tags` in export (compatibility slice vs retired);
- dish-level `meal_composition` and `simple_dish_part` fields (see [MEAL_COMPOSITION.md](MEAL_COMPOSITION.md)).

Implementation order: **taxonomy migrations and target matching → then backup export/import**.

## Purpose

MealRoulette is self-hosted household software. A household must be able to recover its catalog, plan history, settings, and operational data after a bad deploy, broken migration, host failure, or accidental data loss.

Phase 11 provides:

- full JSON export for application-level portability;
- full JSON import for restore into an empty compatible database;
- backup run tracking;
- scheduled backup creation;
- retention cleanup for files under `/backups`;
- optional PostgreSQL dump files for database-level restore;
- documented restore procedure.

## Current Requirements

- Backups are admin-only.
- The Docker Compose stack already mounts `./backups:/backups` for `api` and `worker`.
- JSON export/import is the canonical app-level backup format.
- PostgreSQL dumps are optional operational artifacts, not the canonical cross-version import format.
- Import must validate the full payload before writing any rows.
- Import must not silently merge into a non-empty production database in Phase 11.
- Secrets must not be exported unless explicitly approved by a later product decision.

## Assumptions

- Phase 11 targets restore into an empty database migrated to the same application schema version as the export.
- Backups are local filesystem files under `/backups`; remote backup storage is out of scope.
- Backup files are trusted only after validation. A malformed JSON import must fail before mutation.
- Existing integer primary keys can be preserved during restore because the initial import target is empty.
- Reference data such as units and tags is exported with user data so a restore is self-contained.

## Non-Goals

- Partial import or selective restore.
- Conflict-resolution merge into an already populated database.
- Cross-major-schema migration of old export formats.
- Encrypted backup archives.
- Cloud/S3/WebDAV/Tailscale backup destinations.
- Point-in-time recovery.
- User-facing backup download UI beyond the endpoints needed for Phase 11, unless implementation discovers it is trivial and compatible with the scope.

## Export Format

The JSON export should be deterministic enough for debugging and diffing, but it is not intended as a hand-authored fixture format.

Top-level shape:

```json
{
  "format": "mealroulette.full_export",
  "format_version": 1,
  "app_version": "v0.7.0+",
  "schema_revision": "030_taxonomy_family_backfill",
  "exported_at": "2026-07-13T12:00:00Z",
  "tables": {
    "units": [],
    "tags": [],
    "ingredients": []
  }
}
```

Rules:

- `format` and `format_version` are required.
- `schema_revision` records the Alembic head at export time.
- Datetimes use ISO 8601 with timezone.
- Decimals are serialized as strings to avoid precision loss.
- Enums are serialized by value.
- JSON/JSONB fields are exported as JSON objects or arrays without string encoding.
- Rows inside each table are ordered by primary key, except link tables may be ordered by their composite key.
- Foreign-key references use the exported primary keys in Phase 11.

## Included Data

Export these tables:

| Area | Tables |
| --- | --- |
| Users | `users` |
| Catalog | `units`, `food_groups`, `ingredient_families`, `tags`, `ingredients`, `ingredient_aliases`, `ingredient_unit_conversions`, `dishes`, `dish_tags`, `dish_seasonality`, `recipes`, `recipe_steps`, `recipe_ingredients` |
| Planning | `meal_plans`, `meal_plan_items`, `meal_ratings` |
| Shopping | `shopping_lists`, `shopping_list_items` |
| Telegram | `telegram_settings`, `telegram_subscribers` |
| Scheduler | `planning_rules`, `scheduler_settings` |
| Cooking | `cooking_timer_alerts` |
| Backups | `backup_settings`, `backup_runs` after the Phase 11 migration exists |

Exporting `cooking_timer_alerts` preserves pending operational state. On restore, the worker may process still-pending alerts if their `fire_at` is in the future; expired pending alerts should remain visible as historical state and may be handled by the existing alert processor.

## Excluded Data

Do not export:

- `refresh_tokens`, because active sessions should not survive restore;
- `TELEGRAM_BOT_TOKEN`, because the token is an environment secret and is not stored in the database today;
- `.env` values or Docker Compose secrets;
- generated PostgreSQL internal metadata;
- files outside `/backups`.

User `password_hash` is exported. This is required for a full local restore where existing users can sign in after import. The restore documentation must state that JSON backups are sensitive and should be protected like database dumps.

## Backup Run Tracking

Add a `backup_runs` table.

Fields:

- `id`
- `backup_type`: `json_export` or `pg_dump`
- `status`: `running`, `succeeded`, `failed`
- `file_path`
- `file_size_bytes`
- `checksum_sha256`
- `started_at`
- `finished_at`
- `error_message`
- `created_at`

Recommendations:

- Store paths relative to `/backups` when possible.
- Record failed runs even when no file was produced.
- Use SHA-256 for completed files so restores can verify file integrity before import.
- `backup_type` and `status` should be enum types, matching existing enum usage in the model layer.
- JSON export snapshots are taken **before** the current backup run row is created, and exports omit `backup_runs` rows that are still `running` or lack a `file_path`. A backup file therefore contains only completed prior runs, not the in-flight run that produced it.

## Backup file validation

When reviewing a JSON backup manually:

1. **Shape** — `format`, `format_version`, `schema_revision`, and `tables` must be present and parse as valid JSON.
2. **Taxonomy** — `food_groups`, `ingredient_families`, and `ingredients` should be present. Every ingredient with a non-null `family` should have a matching `family_id` FK after migration `030_taxonomy_family_backfill` (re-run `seed_taxonomy_data` or `alembic upgrade head` on older databases).
3. **Secrets** — `refresh_tokens` must not appear. Treat exports as sensitive because `users.password_hash` is included.
4. **PostgreSQL dump** — `include_pg_dump` defaults to `false`. Expect `mealroulette-pg-*.dump` files only when that setting is enabled and `pg_dump` is available in the API/worker container.
5. **Backup runs** — Rows in `tables.backup_runs` should be completed runs with `file_path` and `checksum_sha256` set; the file being validated does not include its own run record.

## Backup Settings

Add a singleton `backup_settings` table rather than relying only on environment variables.

Fields:

- `id`
- `enabled`
- `run_time`
- `timezone`
- `retention_days`
- `backup_path`
- `include_json_export`
- `include_pg_dump`
- `last_backup_at`
- `last_error`
- `created_at`
- `updated_at`

Defaults:

- `enabled`: `false`
- `run_time`: `03:00`
- `timezone`: `Europe/Paris`
- `retention_days`: `30`
- `backup_path`: `/backups`
- `include_json_export`: `true`
- `include_pg_dump`: `false`

`backup_path` should be validated to stay inside `/backups` in the Docker deployment. A later deployment-specific extension can allow a different mounted path.

## API Surface

All endpoints require authentication. **Admin role is required** for export, import, backup settings, manual backup execution, and backup run listing. Non-admin authenticated users receive `403 Forbidden`.

| Endpoint | Auth | Behaviour |
| --- | --- | --- |
| `GET /api/export/full` | Admin | Return the current full JSON export (includes password hashes). |
| `POST /api/import/full` | Admin | Validate and import a full JSON export into an empty database. |
| `POST /api/backups/run` | Admin | Run the enabled backup types immediately and return created `backup_runs`. |
| `GET /api/backups` | Admin | List backup run records, newest first. |
| `GET /api/backups/settings` | Admin | Return backup settings. |
| `PUT /api/backups/settings` | Admin | Update backup settings. |

The original product spec only lists the first four endpoints. The two settings endpoints are recommended because scheduled backup behaviour otherwise has no admin API equivalent to Telegram and scheduler settings.

## Import Semantics

Phase 11 import is full restore into an empty application database.

Preflight validation must check:

- supported `format` and `format_version`;
- compatible `schema_revision`;
- all required table arrays exist;
- row payloads match expected schemas;
- required unique keys are not duplicated inside the payload;
- foreign-key references resolve inside the payload;
- referenced enums are valid;
- at least one admin user exists;
- target database is empty except for Alembic metadata and allowed singleton defaults.

Import execution rules:

- Run in one database transaction.
- Disable normal service-level side effects such as Telegram sends.
- Insert rows in dependency order.
- Preserve primary keys for Phase 11.
- Reset database sequences after import.
- Do not import refresh tokens.
- Roll back the entire transaction on any error.

Recommended insertion order:

1. `users`
2. `units`
3. `food_groups`
4. `ingredient_families`
5. `tags`
6. `ingredients`
7. `ingredient_aliases`
8. `ingredient_unit_conversions`
9. `dishes`
10. `dish_tags`
11. `dish_seasonality`
12. `recipes`
13. `recipe_steps`
14. `recipe_ingredients`
15. `meal_plans`
16. `meal_plan_items`
17. `meal_ratings`
18. `shopping_lists`
19. `shopping_list_items`
20. `telegram_settings`
21. `telegram_subscribers`
22. `planning_rules`
23. `scheduler_settings`
24. `cooking_timer_alerts`
25. `backup_settings`
26. `backup_runs`

## Scheduled Backups

The worker should add a scheduled backup job similar to the existing scheduled Telegram reminder and meal roulette jobs.

Behaviour:

1. Poll once per minute.
2. Read `backup_settings`.
3. Skip when disabled.
4. Resolve local time using `timezone`.
5. Run once per configured local day at `run_time`.
6. Create JSON export when `include_json_export` is true.
7. Create PostgreSQL dump when `include_pg_dump` is true and `pg_dump` is available.
8. Write files under `/backups`.
9. Record one `backup_run` per artifact.
10. Delete backup files older than `retention_days`.
11. Update `last_backup_at` or `last_error`.

Use atomic file creation:

- write to a temporary file in `/backups`;
- fsync/close where practical;
- compute checksum;
- rename to the final filename only after successful completion.

Recommended file names:

- `mealroulette-full-YYYYMMDD-HHMMSSZ.json`
- `mealroulette-pg-YYYYMMDD-HHMMSSZ.dump`

## PostgreSQL Dump

`pg_dump` is operationally useful for exact restore but should not replace JSON export.

Recommendations:

- Use custom format (`pg_dump --format=custom`) when available.
- Derive connection details from `DATABASE_URL`.
- Do not log database passwords.
- If `pg_dump` is unavailable, record a failed `backup_run` with a clear error and continue JSON backup if enabled.

## Retention

Retention cleanup applies only to files created by MealRoulette backup jobs under `/backups`.

Rules:

- Delete files whose timestamp or `backup_run.created_at` is older than `retention_days`.
- Do not delete unknown filenames.
- Mark missing files in backup listing if a `backup_run` record points to a file that no longer exists.
- Keep failed run records even when files are deleted.

## Frontend Scope

Minimum Phase 11 UI:

- admin settings page for backup schedule and retention;
- manual "Run backup now" action;
- list of recent backup runs with status, type, timestamp, file size, and error message.

Optional if implementation cost is low:

- direct JSON export download button;
- import upload form with strong warning that Phase 11 import requires an empty database.

## Restore Documentation

Add operational documentation covering:

- where files are stored on the host (`./backups`);
- how to run a JSON export manually;
- how to restore JSON into a fresh migrated database;
- how to restore a PostgreSQL dump if enabled;
- how to verify checksum;
- how to rotate or copy backups off-device;
- why JSON backups contain password hashes and must be protected.

## Tests

Backend unit tests:

- export serializer preserves decimals, datetimes, enums, and JSON fields;
- export excludes refresh tokens;
- import validator rejects malformed shape before mutation;
- import validator rejects unresolved foreign keys;
- import validator rejects payloads with no admin user;
- retention cleanup only deletes known backup files;
- scheduled backup runs at most once per configured local day.

Backend integration tests:

- admin can export full JSON;
- non-admin cannot export/import/run backups;
- full export from populated test data imports into an empty database and preserves domain relationships;
- import into non-empty database is rejected;
- manual backup writes files under `/backups` and records successful `backup_runs`;
- failed `pg_dump` records a failed `backup_run` without deleting JSON backup output.

Frontend tests:

- backup settings form loads and saves values;
- manual run action displays success and failure states;
- backup run list renders succeeded and failed rows.

## Acceptance Criteria

- JSON export includes all required Phase 11 domain data.
- JSON import validates the whole payload before writing.
- JSON import restores a full export into an empty compatible database.
- Refresh tokens and environment secrets are not exported.
- Backup files are written only under `/backups`.
- Manual backup creates run records and files.
- Scheduled backup follows configured time, timezone, and retention.
- Restore procedure is documented.
- Relevant backend and frontend tests pass.

## Open Decisions

- Whether JSON import should ever support merge/upsert into a non-empty database.
- Whether backup files should be downloadable from the UI or only through the mounted folder.
- Whether `include_pg_dump` should default to true once Docker images guarantee `pg_dump` availability.
- Whether backup archives should be encrypted in a future phase.
