#!/usr/bin/env sh
set -eu

cd "$(dirname "$0")/.."

if [ ! -x .venv/bin/uvicorn ]; then
  echo "Backend virtual environment is missing. Follow the setup steps in README.md." >&2
  exit 1
fi

exec .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8001 --env-file .env
