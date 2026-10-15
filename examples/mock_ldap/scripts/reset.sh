#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" != "--yes-delete-data" ]]; then
  echo 'This permanently deletes mock LDAP volumes.' >&2
  echo 'Run: ./scripts/reset.sh --yes-delete-data' >&2
  exit 2
fi

cd "$(dirname "$0")/.."

docker compose --profile ui down --volumes
docker compose up -d ldap
./scripts/smoke-test.sh
