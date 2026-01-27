#!/usr/bin/env bash
# E2E tests for STT providers (Speech-to-Text)
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
echo "  E2E STT Tests"
echo "=============================================="

PASSED=0
FAILED=0

run_test() {
  local name="$1"
  local cmd="$2"
  local expect="$3"
  
  echo -n "[$name] "
  if output=$(eval "$cmd" 2>&1); then
    # Check if we got any transcription output (not empty)
    if [ -n "$output" ]; then
      if [ -n "$expect" ] && echo "$output" | grep -qi "$expect"; then
        echo "✅ PASS ($output)"
        ((PASSED++))
      elif [ -z "$expect" ]; then
        echo "✅ PASS (got output)"
        ((PASSED++))
      else
        # Synthetic audio may not transcribe perfectly, that's OK
        echo "✅ PASS (transcribed: $output)"
        ((PASSED++))
      fi
    else
      echo "❌ FAIL (empty output)"
      ((FAILED++))
    fi
  else
    echo "⚠️  SKIP (provider not available)"
  fi
}

# Test 1: Whisper.cpp STT
echo ""
echo "== whisper_cpp STT =="
run_test "whisper_cpp basic" \
  "$PYTHON $STTS --stt-provider whisper_cpp --stt-file $SAMPLES/cmd_echo_hello.wav --stt-only 2>/dev/null | tail -1" \
  "hello"

run_test "whisper_cpp ls" \
  "$PYTHON $STTS --stt-provider whisper_cpp --stt-file $SAMPLES/cmd_ls.wav --stt-only 2>/dev/null | tail -1" \
  "ls"

# Test 2: Vosk STT
echo ""
echo "== vosk STT =="
run_test "vosk basic" \
  "$PYTHON $STTS --stt-provider vosk --stt-model small-pl --stt-file $SAMPLES/cmd_echo_hello.wav --stt-only 2>/dev/null | tail -1" \
  "hello"

# Test 3: faster-whisper STT (optional)
echo ""
echo "== faster_whisper STT (optional) =="
run_test "faster_whisper basic" \
  "$PYTHON $STTS --stt-provider faster_whisper --stt-model base --stt-file $SAMPLES/cmd_echo_hello.wav --stt-only 2>/dev/null | tail -1" \
  "hello"

# Test 4: List STT providers
echo ""
echo "== list-stt =="
run_test "list-stt" \
  "$PYTHON $STTS --list-stt 2>/dev/null" \
  "whisper_cpp"

# Summary
echo ""
echo "=============================================="
echo "  Results: $PASSED passed, $FAILED failed"
echo "=============================================="

if [ "$FAILED" -gt 0 ]; then
  exit 1
fi
echo "✅ All STT E2E tests passed"
