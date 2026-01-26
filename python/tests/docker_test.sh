#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"

echo "== Generating samples =="
"$ROOT/scripts/generate_samples.sh"

export STTS_MOCK_STT=1

echo "== STT only (mock) =="
python3 "$ROOT/stts" --stt-file "$ROOT/samples/cmd_echo_hello.wav" --stt-only | grep -q "echo hello"

echo "== STT once (mock, pipeline mode) =="
python3 "$ROOT/stts" --stt-file "$ROOT/samples/cmd_echo_hello.wav" --stt-once | grep -q "echo hello"

echo "== Execute from STT file (mock) =="
out=$(python3 "$ROOT/stts" --stt-file "$ROOT/samples/cmd_echo_hello.wav")
echo "$out" | grep -q "hello"

echo "== Placeholder {STT} (mock, dry-run) =="
out=$(python3 "$ROOT/stts" --stt-file "$ROOT/samples/cmd_echo_hello.wav" --dry-run echo "{STT}")
echo "$out" | grep -q "echo hello"

echo "== Execute ls from STT file (mock) =="
out=$(python3 "$ROOT/stts" --stt-file "$ROOT/samples/cmd_ls.wav")
echo "$out" | grep -q "README.md"

echo "== STT stream shell (mock, placeholder, dry-run) =="
out=$(python3 "$ROOT/stts" --stt-file "$ROOT/samples/cmd_echo_hello.wav" --stt-stream-shell --cmd "echo '{STT_STREAM}'" --dry-run)
echo "$out" | grep -q "echo hello"

if python3 -c "import nlp2cmd" >/dev/null 2>&1; then
  echo "== NLP2CMD fast-path (optional, dry-run) =="
  out=$(STTS_NLP2CMD_ENABLED=1 STTS_NLP2CMD_PARALLEL=1 STTS_NLP2CMD_CONFIRM=0 \
    python3 "$ROOT/stts" --stt-file "$ROOT/samples/cmd_ls.wav" nlp2cmd -r "{STT}" --auto-confirm --dry-run)
  test -n "$out"
fi

if [ -n "${STTS_DEEPGRAM_KEY:-}" ]; then
  echo "== Deepgram STT (optional, online) =="
  out=$(STTS_MOCK_STT=0 STTS_STT_PROVIDER=deepgram python3 "$ROOT/stts" --stt-file "$ROOT/samples/cmd_ls.wav" --stt-only)
  test -n "$out"
fi

echo "✅ docker_test passed"
