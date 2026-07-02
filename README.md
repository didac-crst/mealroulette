# MealRoulette

MealRoulette is a self-hosted household meal planning app for deciding what to eat, planning lunch and dinner, generating shopping lists, sending Telegram reminders, and cooking from structured recipe steps.

This repository currently contains the project specification and implementation roadmap intended for iterative development in Cursor.

## Documentation

- [Full specification](SPECS.md)
- [Cursor implementation roadmap](docs/CURSOR_ROADMAP.md)
- [MVP scope](docs/MVP.md)

## Target Stack

- Backend: Python 3.12+, FastAPI, Pydantic, SQLAlchemy, Alembic
- Database: PostgreSQL
- Worker: APScheduler
- Frontend: React + Vite
- Deployment: Docker Compose, suitable for Raspberry Pi

## Target Services

```text
api       FastAPI backend
worker    APScheduler jobs for Telegram reminders and backups
frontend  Responsive web UI
db        PostgreSQL
```

## Initial Development Flow

Use the roadmap as the implementation guide:

1. Read `SPECS.md`.
2. Follow `docs/CURSOR_ROADMAP.md` phase by phase.
3. Start with Phase 0 and Phase 1.
4. Keep schema migrations, unit tests, integration tests, pre-commit checks, and Docker Compose working at each phase.

## Developer Commands

```bash
cp .env.example .env
docker compose up --build
make test
```

Backend only:

```bash
cd backend
pip install ".[dev]"
pytest
alembic upgrade head
```

Frontend only:

```bash
cd frontend
npm install
npm run dev
npm test -- --run
```

Install pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
```

Integration tests expect PostgreSQL at `TEST_DATABASE_URL`. The easiest local setup is `docker compose up db`.

## Suggested Cursor Prompt

```text
Read SPECS.md and docs/CURSOR_ROADMAP.md.

Implement Phase 0 and Phase 1 only:
- FastAPI backend with /health
- SQLAlchemy 2.x database setup
- Alembic setup
- PostgreSQL connection through DATABASE_URL
- Docker Compose with api, worker placeholder, frontend placeholder, and db
- React + Vite frontend shell that can display API health status
- .env.example
- basic backend unit and integration tests
- pre-commit hook and CI workflow that run tests on commit and push

Do not implement domain models yet except what is necessary for Alembic/bootstrap.
Keep the repository structure aligned with docs/CURSOR_ROADMAP.md.
```

## Product Summary

MealRoulette is an API-first, Dockerized FastAPI/PostgreSQL application with a responsive frontend, APScheduler worker, Telegram reminder integration, structured recipe data, ingredient normalization, tag-based classification, and an explainable rule-based meal scheduler.
