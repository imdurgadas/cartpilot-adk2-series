#!/usr/bin/env bash
# Part 18 — daily Postgres backup, no managed-database "automatic
# backups" checkbox to rely on. Wire this into cron:
#   0 3 * * * /path/to/cartpilot/scripts/backup.sh >> /var/log/cartpilot-backup.log 2>&1
set -euo pipefail

cd "$(dirname "$0")/.."
source .env

BACKUP_DIR="${BACKUP_DIR:-./backups}"
mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUT_FILE="$BACKUP_DIR/cartpilot_sessions_${TIMESTAMP}.sql.gz"

docker compose exec -T postgres \
  pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "$OUT_FILE"

echo "Backup written to $OUT_FILE"

# Keep the last 14 days of backups, delete anything older.
find "$BACKUP_DIR" -name 'cartpilot_sessions_*.sql.gz' -mtime +14 -delete
