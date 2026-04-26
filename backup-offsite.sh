#!/bin/bash
set -euo pipefail

BACKUP_DIR="/opt/centralmemory/backups"
REMOTE_DIR="gdrive:Backups/contabo-vps/centralmemory"
LOG_FILE="/var/log/cm-backup.log"
RETENTION_REMOTE=14

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

LATEST=$(find "$BACKUP_DIR" -name 'centralmemory-*.sql.gz' -type f -printf '%T+ %p\n' | sort -r | head -n1 | awk '{print $2}')

if [ -z "$LATEST" ]; then
    log "Offsite: no local backup found to upload"
    exit 1
fi

log "Offsite: uploading $(basename $LATEST) to gdrive..."

if rclone copy "$LATEST" "$REMOTE_DIR/" --log-level INFO --log-file="$LOG_FILE" 2>&1; then
    log "Offsite: upload OK"
else
    log "Offsite: upload FAILED"
    exit 1
fi

rclone delete "$REMOTE_DIR/centralmemory-*.sql.gz" --min-age ${RETENTION_REMOTE}d --log-level INFO --log-file="$LOG_FILE" 2>/dev/null || true

log "Offsite: done"
