#!/bin/sh
set -e

# Имя БД: можно переопределить через переменные окружения
DB_NAME=${DB_NAME:-examstats}
BACKUP_PATH=${BACKUP_PATH:-/backup/exam-stats.backup}

echo "⏳ Waiting for PostgreSQL to be ready..."
until pg_isready -U "$POSTGRES_USER"; do
  sleep 1
done

# Проверка наличия базы
if psql -U "$POSTGRES_USER" -tAc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1; then
  echo "✅ Database '$DB_NAME' already exists, skipping restore"
else
  echo "🛠 Creating database: $DB_NAME..."
  createdb -U "$POSTGRES_USER" "$DB_NAME"

  echo "📂 Restoring backup into '$DB_NAME'..."
  pg_restore -U "$POSTGRES_USER" -d "$DB_NAME" "$BACKUP_PATH"

  echo "✅ Restore complete"
fi
