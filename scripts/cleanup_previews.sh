#!/usr/bin/env bash
# Remove preview directories older than 14 days.
set -euo pipefail

PREVIEWS_DIR=${1:-/var/www/dc/previews}
RETENTION_DAYS=${RETENTION_DAYS:-14}

if [[ ! -d "$PREVIEWS_DIR" ]]; then
  echo "Directory $PREVIEWS_DIR does not exist, skipping cleanup" >&2
  exit 0
fi

find "$PREVIEWS_DIR" -maxdepth 1 -type d -name 'pr-*' -mtime +"${RETENTION_DAYS}" -print -exec rm -rf {} +
