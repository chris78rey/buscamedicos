#!/bin/bash
set -euo pipefail

# BuscaMedicos Files Backup Script
# Usage: ./backup_files.sh

BACKUP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../backups"
FILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../files"
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="files_archive_${TIMESTAMP}.tar.gz"

echo "=== Files Backup ==="
echo "Files dir: $FILES_DIR"
echo "Backup dir: $BACKUP_DIR"

if [ ! -d "$FILES_DIR" ]; then
    echo "WARNING: Files directory not found, skipping"
    exit 0
fi

if command -v tar &> /dev/null; then
    tar czf "$BACKUP_DIR/$FILENAME" -C "$(dirname "$FILES_DIR")" "$(basename "$FILES_DIR")"
    SIZE=$(stat -c%s "$BACKUP_DIR/$FILENAME" 2>/dev/null || stat -f%z "$BACKUP_DIR/$FILENAME" 2>/dev/null)
    echo "SUCCESS: Archive created ($SIZE bytes)"
    echo "File: $BACKUP_DIR/$FILENAME"
else
    echo "ERROR: tar not found"
    exit 1
fi
