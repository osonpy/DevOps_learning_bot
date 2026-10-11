#!/bin/sh
# Kunlik pg_dump (docker-compose `backup` servisi).
#   - har kuni BACKUP_HOUR (UTC) dan keyin bir marta: /backups/<db>_YYYY-MM-DD.sql.gz
#   - BACKUP_KEEP_DAYS kundan eskilari o'chiriladi
#   - qo'lda darhol:  docker compose run --rm backup now
# Ulanish: PGHOST/PGUSER/PGPASSWORD/PGDATABASE (compose beradi).
set -eu
set -o pipefail

DIR=${BACKUP_DIR:-/backups}
KEEP=${BACKUP_KEEP_DAYS:-7}
HOUR=${BACKUP_HOUR:-3}

today_file() { echo "$DIR/${PGDATABASE}_$(date -u +%Y-%m-%d).sql.gz"; }

dump() {
  f=$(today_file)
  pg_dump --clean --if-exists --no-owner | gzip > "$f.tmp"
  mv "$f.tmp" "$f"
  echo "backup: $f ($(du -h "$f" | cut -f1))"
  find "$DIR" -name "${PGDATABASE}_*.sql.gz" -mtime +$((KEEP - 1)) -print -delete
}

if [ "${1:-}" = "now" ]; then
  dump
  exit 0
fi

echo "backup: har kuni ${HOUR}:00 UTC dan keyin, ${KEEP} kun saqlanadi -> $DIR"
while true; do
  if [ ! -f "$(today_file)" ] && [ "$(date -u +%H)" -ge "$HOUR" ]; then
    dump || { echo "backup XATO" >&2; rm -f "$(today_file).tmp"; }
  fi
  sleep 300
done
