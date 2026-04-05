#!/bin/bash
set -euo pipefail

# BuscaMedicos Smoke Test Script
# Usage: ./smoke_test.sh [api_base_url]
# Default API base: http://localhost:8000

API_BASE="${1:-http://localhost:8000}"
FAILED=0

echo "=== BuscaMedicos Smoke Tests ==="
echo "API: $API_BASE"
echo ""

test_endpoint() {
    local NAME="$1"
    local URL="$2"
    local EXPECTED="$3"
    local METHOD="${4:-GET}"
    
    echo -n "Test: $NAME ... "
    RESPONSE=$(curl -sf -X "$METHOD" "$URL" 2>/dev/null || echo "FAILED")
    
    if echo "$RESPONSE" | grep -q "$EXPECTED"; then
        echo "PASS"
    else
        echo "FAIL (got: $RESPONSE)"
        FAILED=$((FAILED + 1))
    fi
}

echo "--- Health Endpoints ---"
test_endpoint "Health Live" "$API_BASE/health/live" "ok"
test_endpoint "Version" "$API_BASE/version" "version"

echo ""
echo "--- Auth Endpoints ---"
test_endpoint "Register Patient" "$API_BASE/api/v1/auth/register/patient" "" "POST"
test_endpoint "Register Professional" "$API_BASE/api/v1/auth/register/professional" "" "POST"
test_endpoint "Login" "$API_BASE/api/v1/auth/login" "" "POST"

echo ""
echo "--- Public Endpoints ---"
test_endpoint "Specialties" "$API_BASE/api/v1/public/specialties" ""

echo ""
echo "--- Result: $FAILED failures ---"

if [ $FAILED -eq 0 ]; then
    echo "=== ALL SMOKE TESTS PASSED ==="
    exit 0
else
    echo "=== SMOKE TESTS FAILED ==="
    exit 1
fi
