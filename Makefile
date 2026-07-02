.PHONY: test test-unit test-integration test-backend test-frontend up down test-db-setup free-ports

test: test-db-setup test-backend test-frontend

test-unit:
	cd backend && python3.12 -m pytest -m "not integration"

test-integration: test-db-setup
	cd backend && python3.12 -m pytest -m integration
	cd frontend && npm test -- --run

test-backend: test-db-setup
	cd backend && python3.12 -m pytest

test-frontend:
	cd frontend && npm test -- --run

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
