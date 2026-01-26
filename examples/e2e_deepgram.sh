#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [ -z "${STTS_DEEPGRAM_KEY:-}" ]; then
  echo "SKIP: set STTS_DEEPGRAM_KEY to run Deepgram check" >&2
  exit 0
fi

echo "== Deepgram STT (online, file-based) =="
STTS_MOCK_STT=0 STTS_STT_PROVIDER=deepgram \
  "$ROOT/stts" --stt-file "$ROOT/python/samples/cmd_ls.wav" --stt-only

echo "✅ deepgram e2e ok"
