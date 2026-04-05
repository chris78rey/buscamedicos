#!/bin/bash
set -euo pipefail

# BuscaMedicos Database Backup Script
# Usage: ./backup_db.sh

BACKUP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../backups"
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="pg_dump_${TIMESTAMP}.dump"

echo "=== Database Backup ==="
echo "Backup dir: $BACKUP_DIR"
echo "Filename: $FILENAME"

if command -v pg_dump &> /dev/null; then
    DATABASE_URL="${DATABASE_URL:-}"
    if [ -z "$DATABASE_URL" ]; then
        echo "ERROR: DATABASE_URL not set"
        exit 1
    fi
    pg_dump -Fc -f "$BACKUP_DIR/$FILENAME" --dbname "$DATABASE_URL"
    SIZE=$(stat -c%s "$BACKUP_DIR/$FILENAME" 2>/dev/null || stat -f%z "$BACKUP_DIR/$FILENAME" 2>/dev/null)
    echo "SUCCESS: Backup created ($SIZE bytes)"
    echo "File: $BACKUP_DIR/$FILENAME"
else
    echo "ERROR: pg_dump not found. Install PostgreSQL client."
    exit 1
fi
