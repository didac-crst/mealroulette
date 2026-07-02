#!/usr/bin/env bash
set -euo pipefail

PORTS=(3000 8000 5432)

echo "Stopping MealRoulette stack if present..."
docker compose down --remove-orphans 2>/dev/null || true

for port in "${PORTS[@]}"; do
  found=0

  while IFS= read -r container_id; do
    [ -z "${container_id}" ] && continue

    if docker port "${container_id}" 2>/dev/null | grep -qE ":${port}$"; then
      container_name="$(docker inspect --format '{{.Name}}' "${container_id}" | sed 's#^/##')"
      echo "Port ${port}: stopping ${container_name} (${container_id})"
      docker stop "${container_id}" >/dev/null
      found=1
    fi
  done < <(docker ps -q)

  if [ "${found}" -eq 0 ]; then
    echo "Port ${port}: no running containers"
  fi
done

echo "Requested ports are free for MealRoulette."
