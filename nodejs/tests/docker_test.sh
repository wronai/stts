#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"

echo "== Generating samples =="
"$ROOT/scripts/generate_samples.sh"

export STTS_MOCK_STT=1

echo "== STT only (mock) =="
node "$ROOT/stts.mjs" --stt-file "$ROOT/samples/cmd_echo_hello.wav" --stt-only | grep -q "echo hello"

echo "== Execute from STT file (mock) =="
out=$(node "$ROOT/stts.mjs" --stt-file "$ROOT/samples/cmd_echo_hello.wav")
echo "$out" | grep -q "hello"

echo "✅ docker_test passed"
