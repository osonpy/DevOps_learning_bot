#!/usr/bin/env sh
set -eu

echo "▶ migrations..."
alembic upgrade head

echo "▶ seed curriculum..."
python -m src.scripts.seed

echo "▶ start: $*"
exec "$@"
