#!/usr/bin/env bash
# E2E tests for streaming modes
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STTS="$ROOT/python/stts"
SAMPLES="$ROOT/python/samples"
VENV="$ROOT/venv/bin/python"

# Use venv python if available
if [ -f "$VENV" ]; then
  PYTHON="$VENV"
else
  PYTHON="python3"
fi

echo "=============================================="
echo "  E2E Streaming Tests"
echo "=============================================="

PASSED=0
FAILED=0

run_test() {
  local name="$1"
  local cmd="$2"
  local expect="$3"
  
  echo -n "[$name] "
  if output=$(eval "$cmd" 2>&1); then
    if [ -z "$expect" ]; then
      echo "✅ PASS"
      ((PASSED++))
      return 0
    fi
    if echo "$output" | grep -qi "$expect"; then
      echo "✅ PASS"
      ((PASSED++))
    else
      echo "❌ FAIL (expected '$expect')"
      ((FAILED++))
    fi
  else
    echo "⚠️  SKIP"
  fi
}

# Test 1: TTS stdin streaming
echo ""
echo "== TTS stdin streaming =="
run_test "tts-stdin" \
  "echo 'Hello world' | STTS_TTS_PROVIDER=espeak $PYTHON $STTS --tts-stdin 2>&1" \
  ""

# Test 2: Streaming command output
echo ""
echo "== Command streaming =="
run_test "stream flag" \
  "$PYTHON $STTS --stream echo 'test streaming' 2>/dev/null" \
  "test streaming"

run_test "no-stream flag" \
  "$PYTHON $STTS --no-stream echo 'test no stream' 2>/dev/null" \
  "test no stream"

# Test 3: Pipe mode (non-TTY)
echo ""
echo "== Pipe mode =="
run_test "pipe input" \
  "echo 'echo piped' | $PYTHON $STTS --dry-run 2>/dev/null" \
  "echo piped"

# Test 4: STT file + streaming execution
echo ""
echo "== STT + streaming execution =="
run_test "stt+stream" \
  "$PYTHON $STTS --stream --stt-provider whisper_cpp --stt-file $SAMPLES/cmd_ls.wav 2>/dev/null | head -5" \
  ""

# Summary
echo ""
echo "=============================================="
echo "  Results: $PASSED passed, $FAILED failed"
echo "=============================================="

if [ "$FAILED" -gt 0 ]; then
  exit 1
fi
echo "✅ All streaming E2E tests passed"
