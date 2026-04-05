#!/bin/bash
set -euo pipefail

# BuscaMedicos Deployment Script
# Usage: ./deploy.sh <image_tag> <environment>
# Example: ./deploy.sh v1.0.0 production

IMAGE_TAG="${1:-}"
ENVIRONMENT="${2:-production}"

if [ -z "$IMAGE_TAG" ]; then
    echo "Usage: $0 <image_tag> <environment>"
    echo "Example: $0 v1.0.0 production"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend_api"

echo "=== BuscaMedicos Deployment ==="
echo "Image tag: $IMAGE_TAG"
echo "Environment: $ENVIRONMENT"

cd "$PROJECT_ROOT/infra"

if [ ! -f .env.production ]; then
    echo "ERROR: .env.production not found. Copy .env.production.example to .env.production and configure."
    exit 1
fi

echo "Pulling latest code..."
git fetch --tags
git checkout main || true
git pull origin main

RELEASE_CODE="release_${IMAGE_TAG}_$(date +%Y%m%d_%H%M%S)"
GIT_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "")

echo "Building Docker image with tag: $IMAGE_TAG"
docker build -f "$BACKEND_DIR/Dockerfile.prod" \
    -t buscamedicos-backend:"$IMAGE_TAG" \
    "$BACKEND_DIR"

echo "Stopping existing containers..."
docker compose -f docker-compose.prod.yml down || true

echo "Starting services with new image..."
export IMAGE_TAG
docker compose -f docker-compose.prod.yml up -d

echo "Waiting for backend to be healthy..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:8000/health/live > /dev/null 2>&1; then
        echo "Backend is healthy!"
        break
    fi
    echo "Waiting... ($i/30)"
    sleep 2
done

echo "Running smoke tests..."
if curl -sf http://localhost:8000/health/live | grep -q "ok"; then
    echo "PASS: Health check"
else
    echo "FAIL: Health check"
    exit 1
fi

echo "Registering release..."
curl -s -X POST http://localhost:8000/api/v1/admin/ops/releases/register \
    -H "Content-Type: application/json" \
    -d "{\"release_code\": \"$RELEASE_CODE\", \"git_commit\": \"$GIT_COMMIT\", \"image_tag\": \"$IMAGE_TAG\", \"environment\": \"$ENVIRONMENT\"}" \
    || echo "Release registration may require auth"

echo "=== Deployment complete ==="
echo "Release: $RELEASE_CODE"
echo "Tag: $IMAGE_TAG"
