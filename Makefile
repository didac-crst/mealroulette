.PHONY: test test-unit test-integration test-backend test-backend-parallel test-frontend up down test-db-setup free-ports validate-taxonomy apply-conversion-policy reconcile-taxonomy

# Optional test selection. Backend paths are relative to backend/ (e.g. tests/test_catalog.py).
# Frontend paths are relative to frontend/ (e.g. src/features/planning/planFormat.test.ts).
TESTS ?=
FRONTEND_TESTS ?=
# Number of xdist worker databases to create (defaults to CPU count; match pytest -n auto).
PARALLEL_DBS ?= $(shell python3.12 -c "import os; print(os.cpu_count() or 4)")

test: test-db-setup test-backend test-frontend

test-unit:
	cd backend && python3.12 -m pytest -m "not integration" $(TESTS)

test-integration: test-db-setup
	cd backend && python3.12 -m pytest -m integration $(TESTS)
	cd frontend && npm test -- --run $(FRONTEND_TESTS)

test-backend: test-db-setup
	cd backend && python3.12 -m pytest $(TESTS)

test-backend-parallel: test-db-setup
	cd backend && python3.12 -m pytest -n auto $(TESTS)

test-frontend:
	cd frontend && npm test -- --run $(FRONTEND_TESTS)

free-ports:
	./scripts/free-ports.sh

test-db-setup: free-ports
	docker compose up -d db
	@sleep 2
	@PARALLEL_DBS=$(PARALLEL_DBS) python3.12 backend/scripts/setup_test_databases.py

up: free-ports
	docker compose up --build

down:
	docker compose down

validate-taxonomy:
	cd backend && python3.12 -m mealroulette.commands.validate_taxonomy

apply-conversion-policy:
	cd backend && python3.12 -m mealroulette.commands.apply_conversion_policy

reconcile-taxonomy:
	cd backend && python3.12 -m mealroulette.commands.reconcile_taxonomy && python3.12 -m mealroulette.commands.validate_taxonomy
