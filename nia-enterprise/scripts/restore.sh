#!/bin/bash
# Restore from backup

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <backup-file>"
    echo "Available backups:"
    ls -lh backups/nia-enterprise-backup-*.tar.gz 2>/dev/null || echo "No backups found"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "Restoring from backup: $BACKUP_FILE"
echo "WARNING: This will overwrite existing configuration files!"
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Restore cancelled"
    exit 0
fi

# Create backup of current state before restoring
./scripts/backup.sh

# Extract backup
echo "Extracting backup..."
tar -xzf "$BACKUP_FILE"

echo "Restore complete!"
echo "Please verify the configuration before starting services."
