#!/bin/bash
# Backup script for NiA-Enterprise

set -e

BACKUP_DIR="backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="nia-enterprise-backup-${TIMESTAMP}.tar.gz"

mkdir -p "$BACKUP_DIR"

echo "Creating backup..."
echo "Backup name: $BACKUP_NAME"

# Backup configuration files
tar -czf "$BACKUP_DIR/$BACKUP_NAME" \
    config/ \
    k8s/ \
    docker/ \
    --exclude='*.log' \
    --exclude='*.tmp'

echo "Backup created: $BACKUP_DIR/$BACKUP_NAME"
echo "Size: $(du -h "$BACKUP_DIR/$BACKUP_NAME" | cut -f1)"

# Keep only last 10 backups
echo "Cleaning old backups..."
cd "$BACKUP_DIR"
ls -t nia-enterprise-backup-*.tar.gz | tail -n +11 | xargs -r rm -f
echo "Backup retention: $(ls -1 nia-enterprise-backup-*.tar.gz | wc -l) backups kept"

echo "Backup complete!"
