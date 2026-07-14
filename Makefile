.PHONY: test test-unit test-integration test-backend test-frontend up down test-db-setup free-ports validate-taxonomy apply-conversion-policy reconcile-taxonomy

# Optional test selection. Backend paths are relative to backend/ (e.g. tests/test_catalog.py).
# Frontend paths are relative to frontend/ (e.g. src/features/planning/planFormat.test.ts).
TESTS ?=
FRONTEND_TESTS ?=

test: test-db-setup test-backend test-frontend

test-unit:
	cd backend && python3.12 -m pytest -m "not integration" $(TESTS)

test-integration: test-db-setup
	cd backend && python3.12 -m pytest -m integration $(TESTS)
	cd frontend && npm test -- --run $(FRONTEND_TESTS)

test-backend: test-db-setup
	cd backend && python3.12 -m pytest $(TESTS)

test-frontend:
	cd frontend && npm test -- --run $(FRONTEND_TESTS)

free-ports:
	./scripts/free-ports.sh

test-db-setup: free-ports
	docker compose up -d db
	@sleep 2
	@docker exec mealroulette-db psql -U mealroulette -d mealroulette -tc "SELECT 1 FROM pg_database WHERE datname = 'mealroulette_test'" | grep -q 1 || docker exec mealroulette-db psql -U mealroulette -d mealroulette -c "CREATE DATABASE mealroulette_test;"

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
