#!/usr/bin/env sh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$REPO_ROOT/infra"
docker compose up -d

echo ""
echo "Docker services are up (including backend_seed)."
echo "Backend: http://localhost:8000"
echo ""
echo "To launch Flutter web:"
echo "  cd \"$REPO_ROOT/app_flutter\""
echo "  flutter pub get"
echo "  flutter run -d chrome --dart-define=API_BASE_URL=http://localhost:8000/api/v1"