#!/usr/bin/env bash
# End-to-end smoke check of the running stack (Feature 0010, FR7).
#   API_KEY=... scripts/smoke.sh
# Set SMOKE_RATE_LIMIT=<n> when the API runs with RATE_LIMIT_DEFAULT_PER_MINUTE=<n>
# to also verify that HTTP 429 is returned. It does not call the LLM.
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:8501}"
: "${API_KEY:?Set API_KEY}"

failures=0
check() {
  if [ "$2" = "$3" ]; then
    echo "PASS  $1"
  else
    echo "FAIL  $1 (expected $2, got $3)"
    failures=$((failures + 1))
  fi
}
status() { curl -s -o /dev/null -w "%{http_code}" "$@" || echo "000"; }

check "API /health"                 200 "$(status "$API_URL/health")"
check "Missing key is rejected"     422 "$(status "$API_URL/corpus/summary")"
check "Wrong key is rejected"       401 "$(status -H 'X-API-Key: wrong' "$API_URL/corpus/summary")"
check "Valid key is accepted"       200 "$(status -H "X-API-Key: $API_KEY" "$API_URL/corpus/summary")"
check "Frontend health"             200 "$(status "$FRONTEND_URL/_stcore/health")"

if [ -n "${SMOKE_RATE_LIMIT:-}" ]; then
  seen=0
  for _ in $(seq 1 $((SMOKE_RATE_LIMIT + 2))); do
    if [ "$(status -H "X-API-Key: $API_KEY" "$API_URL/corpus/summary")" = "429" ]; then
      seen=1
    fi
  done
  check "Rate limit returns 429"    1 "$seen"
fi

if [ "$failures" -gt 0 ]; then
  echo "$failures check(s) failed"
  exit 1
fi
echo "All checks passed"
