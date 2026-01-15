#!/bin/bash

# Path to the script's current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Path to .env
ENV_FILE="$SCRIPT_DIR/../.env"

# Path to the .backup file
BACKUP_FILE="$SCRIPT_DIR/exam-stats.backup"

# Check if the .backup file exists
if [[ ! -f "$BACKUP_FILE" ]]; then
  echo "Backup file not found: $BACKUP_FILE"
  read -n 1 -s -r -p "Press any key to exit..."
  exit 1
fi

# Check if the .env file exists
if [[ ! -f "$ENV_FILE" ]]; then
  echo ".env file not found: $ENV_FILE"
  read -n 1 -s -r -p "Press any key to exit..."
  exit 1
fi

# Load variables from .env
export $(grep -v '^#' "$ENV_FILE" | xargs)

# Variable assignments
CONTAINER_NAME="examstats-db"
DB_NAME="${DB_NAME:-postgres}"
DB_USER="${POSTGRES_USER:-postgres}"
DB_PASSWORD="${POSTGRES_PASSWORD:-postgres}"

echo ">>> Copying backup to container $CONTAINER_NAME..."
docker cp "$BACKUP_FILE" "$CONTAINER_NAME":/tmp/restore.backup

echo ">>> Restoring database $DB_NAME..."
docker exec -e PGPASSWORD="$DB_PASSWORD" "$CONTAINER_NAME" \
  sh -c "pg_restore -U \"$DB_USER\" -d \"$DB_NAME\" --clean --if-exists /tmp/restore.backup"

echo ">>> Removing temporary file from the container..."
docker exec "$CONTAINER_NAME" sh -c "rm /tmp/restore.backup"

echo "Backup successfully restored in container $CONTAINER_NAME"
