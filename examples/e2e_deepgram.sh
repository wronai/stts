#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STTS="$ROOT/python/stts"
VENV="$ROOT/venv/bin/python"

# Use venv python if available
if [ -f "$VENV" ]; then
  PYTHON="$VENV"
else
  PYTHON="python3"
fi

if [ -z "${STTS_DEEPGRAM_KEY:-}" ]; then
  echo "SKIP: set STTS_DEEPGRAM_KEY to run Deepgram check" >&2
  exit 0
fi

echo "== Deepgram STT (online, file-based) =="
STTS_MOCK_STT=0 STTS_STT_PROVIDER=deepgram \
  $PYTHON "$STTS" --stt-provider deepgram --stt-file "$ROOT/python/samples/cmd_ls.wav" --stt-only

echo "✅ deepgram e2e ok"
