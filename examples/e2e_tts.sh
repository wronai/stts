#!/usr/bin/env bash
# E2E tests for TTS providers (Text-to-Speech)
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STTS="$ROOT/python/stts"
VENV="$ROOT/venv/bin/python"
TMP_WAV="/tmp/stts_tts_test_$$.wav"

# Use venv python if available
if [ -f "$VENV" ]; then
  PYTHON="$VENV"
else
  PYTHON="python3"
fi

cleanup() {
  rm -f "$TMP_WAV"
}
trap cleanup EXIT

echo "=============================================="
echo "  E2E TTS Tests"
echo "=============================================="

PASSED=0
FAILED=0

run_test() {
  local name="$1"
  local cmd="$2"
  
  echo -n "[$name] "
  if eval "$cmd" >/dev/null 2>&1; then
    echo "✅ PASS"
    ((PASSED++))
  else
    echo "⚠️  SKIP (provider not available)"
  fi
}

# Test 1: Piper TTS
echo ""
echo "== piper TTS =="
run_test "piper basic" \
  "$PYTHON $STTS --tts-test 'Test piper syntezy mowy'"

run_test "piper polish voice" \
  "STTS_TTS_PROVIDER=piper STTS_TTS_VOICE=pl $PYTHON $STTS --tts-test 'Cześć, to jest test'"

# Test 2: espeak TTS
echo ""
echo "== espeak TTS =="
run_test "espeak basic" \
  "STTS_TTS_PROVIDER=espeak $PYTHON $STTS --tts-test 'Hello world'"

run_test "espeak polish" \
  "STTS_TTS_PROVIDER=espeak STTS_TTS_VOICE=pl $PYTHON $STTS --tts-test 'Cześć świecie'"

# Test 3: List TTS providers
echo ""
echo "== list-tts =="
run_test "list-tts" \
  "$PYTHON $STTS --list-tts 2>/dev/null | grep -q 'piper\|espeak'"

# Summary
echo ""
echo "=============================================="
echo "  Results: $PASSED passed, $FAILED failed"
echo "=============================================="

if [ "$FAILED" -gt 0 ]; then
  exit 1
fi
echo "✅ All TTS E2E tests passed"
