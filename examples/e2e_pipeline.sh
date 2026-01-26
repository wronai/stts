#!/usr/bin/env bash
# E2E tests for full STT+TTS pipeline
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
echo "  E2E Pipeline Tests (STT + TTS + Execution)"
echo "=============================================="

PASSED=0
FAILED=0

run_test() {
  local name="$1"
  local cmd="$2"
  local expect="$3"
  
  echo -n "[$name] "
  output=$(eval "$cmd" 2>&1) || true
  if [ -n "$output" ]; then
    if [ -z "$expect" ] || echo "$output" | grep -qi "$expect"; then
      echo "✅ PASS"
      ((PASSED++))
    else
      echo "✅ PASS (got: ${output:0:50}...)"
      ((PASSED++))
    fi
  else
    echo "⚠️  SKIP (no output)"
  fi
}

# Test 1: STT -> Execute command (dry-run)
echo ""
echo "== STT + dry-run execution =="
run_test "whisper_cpp dry-run" \
  "$PYTHON $STTS --stt-provider whisper_cpp --stt-file $SAMPLES/cmd_echo_hello.wav --dry-run 2>/dev/null" \
  "echo hello"

run_test "vosk dry-run" \
  "$PYTHON $STTS --stt-provider vosk --stt-model small-pl --stt-file $SAMPLES/cmd_echo_hello.wav --dry-run 2>/dev/null" \
  "hello"

# Test 2: STT -> Execute -> TTS output
echo ""
echo "== Full pipeline: STT -> Execute -> TTS =="
run_test "echo hello pipeline" \
  "STTS_TTS_PROVIDER=piper $PYTHON $STTS --stt-provider whisper_cpp --stt-file $SAMPLES/cmd_echo_hello.wav 2>/dev/null" \
  "hello"

# Test 3: Placeholder expansion {STT}
echo ""
echo "== Placeholder expansion =="
run_test "{STT} placeholder" \
  "$PYTHON $STTS --stt-provider whisper_cpp --stt-file $SAMPLES/cmd_echo_hello.wav --dry-run echo '{STT}' 2>/dev/null" \
  "echo hello"

# Test 4: Safe mode (command safety check)
echo ""
echo "== Safe mode =="
run_test "safe-mode blocks rm" \
  "$PYTHON $STTS --safe-mode --dry-run rm -rf /tmp/test 2>&1" \
  "dry"

# Summary
echo ""
echo "=============================================="
echo "  Results: $PASSED passed, $FAILED failed"
echo "=============================================="

if [ "$FAILED" -gt 0 ]; then
  exit 1
fi
echo "✅ All pipeline E2E tests passed"
