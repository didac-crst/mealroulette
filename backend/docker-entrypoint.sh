#!/bin/sh
set -e

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
  echo "Applying database migrations..."
  alembic upgrade head
fi

if [ "${RUN_REFERENCE_SEED:-true}" = "true" ]; then
  echo "Seeding reference catalog data..."
  python -m mealroulette.commands.seed_reference_data
fi

echo "Starting application: $*"
exec "$@"
