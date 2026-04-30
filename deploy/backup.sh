#!/bin/bash
set -euo pipefail

# BACKUP_BUCKET must be set in the environment or sourced from ~/nest/.env
: "${BACKUP_BUCKET:?BACKUP_BUCKET is not set}"
BUCKET="gs://${BACKUP_BUCKET}/backups"
VM_URL="http://localhost:8428"
KEEP_DAYS=30

# Create a consistent snapshot via VictoriaMetrics API
SNAPSHOT=$(curl -sf "${VM_URL}/snapshot/create" | python3 -c "import sys,json; print(json.load(sys.stdin)['snapshot'])")

# Stream snapshot from container directly to GCS (no temp file needed)
BACKUP_NAME="vm-$(date +%Y%m%d).tar.gz"
docker exec nest-victoriametrics-1 tar -czf - "/storage/snapshots/${SNAPSHOT}" | \
  gsutil cp - "${BUCKET}/${BACKUP_NAME}"

# Delete the snapshot from VictoriaMetrics
curl -sf "${VM_URL}/snapshot/delete?snapshot=${SNAPSHOT}" > /dev/null

# Prune backups older than KEEP_DAYS
gsutil ls "${BUCKET}/" | while read -r obj; do
  obj_date=$(basename "$obj" | grep -oP '\d{8}' || true)
  if [[ -n "$obj_date" ]]; then
    cutoff=$(date -d "-${KEEP_DAYS} days" +%Y%m%d)
    if [[ "$obj_date" < "$cutoff" ]]; then
      gsutil rm "$obj"
    fi
  fi
done

echo "$(date -Iseconds) backup complete: ${BACKUP_NAME}"
