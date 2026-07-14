#!/usr/bin/env python3
"""Create sequential and xdist worker PostgreSQL databases for backend tests."""

from __future__ import annotations

import os

import psycopg
from psycopg import sql


def _database_names(parallel_dbs: int) -> list[str]:
    return ["mealroulette_test", *[f"mealroulette_test_gw{index}" for index in range(parallel_dbs)]]


def _admin_database_url() -> str:
    return os.environ.get(
        "ADMIN_DATABASE_URL",
        "postgresql://mealroulette:mealroulette@localhost:5432/mealroulette",
    )


def setup_test_databases(*, parallel_dbs: int | None = None) -> list[str]:
    worker_count = parallel_dbs if parallel_dbs is not None else int(os.environ.get("PARALLEL_DBS", os.cpu_count() or 4))
    names = _database_names(worker_count)

    with psycopg.connect(_admin_database_url(), autocommit=True) as connection:
        with connection.cursor() as cursor:
            for name in names:
                cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,))
                if cursor.fetchone() is not None:
                    continue
                cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
                print(f"Created database {name}")

    return names


def main() -> None:
    created = setup_test_databases()
    print(f"Test databases ready ({len(created)}): {', '.join(created)}")


if __name__ == "__main__":
    main()
