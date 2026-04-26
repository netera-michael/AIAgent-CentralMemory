#!/bin/bash
set -euo pipefail

DB_CONTAINER="centralmemory-postgres"
DB_USER="centralmemory"
DB_NAME="centralmemory"
BACKUP_DIR="/opt/centralmemory/backups"
RETENTION_COUNT=24
LOG_FILE="/var/log/cm-backup.log"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/centralmemory-${TIMESTAMP}.sql.gz"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

log "Local backup starting..."

mkdir -p "$BACKUP_DIR"

if docker exec "$DB_CONTAINER" pg_dump -U "$DB_USER" -d "$DB_NAME" | gzip > "$BACKUP_FILE" 2>>"$LOG_FILE"; then
    FILESIZE=$(stat -c%s "$BACKUP_FILE" 2>/dev/null || echo 0)
    if [ "$FILESIZE" -lt 1024 ]; then
        log "ERROR: Backup file too small (${FILESIZE} bytes), likely failed"
        rm -f "$BACKUP_FILE"
        exit 1
    fi
    if gzip -t "$BACKUP_FILE" 2>/dev/null; then
        log "Backup OK: $(basename $BACKUP_FILE) (${FILESIZE} bytes)"
    else
        log "ERROR: Backup gzip integrity check failed"
        rm -f "$BACKUP_FILE"
        exit 1
    fi
else
    log "ERROR: pg_dump failed"
    exit 1
fi

COUNT=$(find "$BACKUP_DIR" -name 'centralmemory-*.sql.gz' -type f | wc -l)
if [ "$COUNT" -gt "$RETENTION_COUNT" ]; then
    PRUNE=$((COUNT - RETENTION_COUNT))
    find "$BACKUP_DIR" -name 'centralmemory-*.sql.gz' -type f -printf '%T+ %p\n' | sort | head -n "$PRUNE" | awk '{print $2}' | xargs rm -f
    log "Pruned ${PRUNE} old backups (retention: ${RETENTION_COUNT})"
fi

log "Local backup done"
