#!/usr/bin/env bash
# Run all E2E tests
set -uo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "╔════════════════════════════════════════════╗"
echo "║       STTS E2E Test Suite                  ║"
echo "╚════════════════════════════════════════════╝"
echo ""

TOTAL_PASSED=0
TOTAL_FAILED=0

run_suite() {
  local name="$1"
  local script="$2"
  
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "▶ Running: $name"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  
  if bash "$script"; then
    echo ""
  else
    echo "⚠️  Some tests in $name failed"
    echo ""
  fi
}

# Run all test suites
run_suite "STT Tests" "$ROOT/e2e_stt.sh"
run_suite "TTS Tests" "$ROOT/e2e_tts.sh"
run_suite "Pipeline Tests" "$ROOT/e2e_pipeline.sh"
run_suite "Streaming Tests" "$ROOT/e2e_streaming.sh"

# Optional: Deepgram (requires API key)
if [ -n "${STTS_DEEPGRAM_KEY:-}" ]; then
  run_suite "Deepgram Tests" "$ROOT/e2e_deepgram.sh"
else
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "⏭  SKIP: Deepgram (set STTS_DEEPGRAM_KEY to enable)"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
fi

echo ""
echo "╔════════════════════════════════════════════╗"
echo "║  ✅ All E2E test suites completed          ║"
echo "╚════════════════════════════════════════════╝"
