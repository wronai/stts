#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"

if [ -z "${STTS_SKIP_SAMPLE_GEN:-}" ]; then
  if command -v espeak >/dev/null 2>&1; then
    echo "== Generating samples =="
    "$ROOT/scripts/generate_samples.sh"
  else
    echo "== Skipping sample generation (espeak not found) =="
  fi
fi

export STTS_MOCK_STT=1
export STTS_NLP2CMD_ENABLED=0
export STTS_NLP2CMD_CONFIRM=0

echo "== STT only (mock) =="
node "$ROOT/stts.mjs" --stt-file "$ROOT/samples/cmd_echo_hello.wav" --stt-only | grep -q "echo hello"

echo "== Execute from STT file (mock) =="
out=$(node "$ROOT/stts.mjs" --stt-file "$ROOT/samples/cmd_echo_hello.wav")
echo "$out" | grep -q "hello"

echo "== Execute ls from STT file (mock) =="
out=$(node "$ROOT/stts.mjs" --stt-file "$ROOT/samples/cmd_ls.wav")
echo "$out" | grep -q "README.md"

echo "✅ docker_test passed"
