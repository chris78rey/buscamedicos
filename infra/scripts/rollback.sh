#!/bin/bash
set -euo pipefail

# BuscaMedicos Rollback Script
# Usage: ./rollback.sh <release_id>
# Example: ./rollback.sh abc123-def456

RELEASE_ID="${1:-}"
if [ -z "$RELEASE_ID" ]; then
    echo "Usage: $0 <release_id>"
    echo "Find release IDs: GET /api/v1/admin/ops/releases"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== BuscaMedicos Rollback ==="
echo "Target release ID: $RELEASE_ID"

echo "Marking release as rolled back..."
RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/admin/ops/releases/$RELEASE_ID/mark-rollback")
echo "Response: $RESPONSE"

echo "For full rollback: docker compose -f $PROJECT_ROOT/infra/docker-compose.prod.yml down"
echo "Then redeploy with previous image tag"
echo "=== Rollback marked ==="
