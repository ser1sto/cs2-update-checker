#!/bin/bash

set -euo pipefail

set -o allexport
source "$(dirname "$0")/.env"
set +o allexport

echo "===== $(date) =====" >> "$LOG_PATH"

docker pull seristo/cs2-update-docker:arm64 >> "$LOG_PATH" 2>&1

docker run --rm \
  --env-file "$APP_PATH/.env" \
  seristo/cs2-update-docker:arm64 >> "$LOG_PATH" 2>&1

echo "" >> "$LOG_PATH"
