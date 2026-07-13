# Restore procedure (Phase 11)

Operational notes for recovering a MealRoulette household from backups under `./backups` (mounted to `/backups` in Docker).

## JSON export (canonical)

1. Stop the API and worker containers to avoid writes during restore.
2. Create a fresh PostgreSQL database and run migrations to the same schema revision as the export (`schema_revision` field in the JSON file).
3. Confirm the database is empty (no users, dishes, or ingredients).
4. Import via admin API: `POST /api/import/full` with the JSON body, or use a scripted client.
5. Restart API and worker.

JSON backups include `password_hash` values so existing users can sign in. Treat files like database dumps — restrict filesystem access.

## PostgreSQL dump (optional)

When `include_pg_dump` is enabled, restore with:

```bash
pg_restore --clean --if-exists --dbname="$DATABASE_URL" mealroulette-pg-YYYYMMDD-HHMMSSZ.dump
```

Use dumps only when the PostgreSQL major version matches the source host. Prefer JSON export for cross-version portability.

## Verification

- Compare `checksum_sha256` on the `backup_runs` record with `sha256sum` on the file before import.
- After JSON import, spot-check dish count, active plan week, and scheduler settings in the UI.

## Off-site copies

Copy `./backups` to another machine or storage periodically. Remote destinations are out of scope for Phase 11 but recommended for real deployments.
