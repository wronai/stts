#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STTS="$ROOT/python/stts"
SAMPLE="$ROOT/python/samples/cmd_make_build.wav"
VENV_PY="$ROOT/venv/bin/python"

if [ -f "$VENV_PY" ]; then
  PYTHON="$VENV_PY"
else
  PYTHON="python3"
fi

if ! command -v nlp2cmd >/dev/null 2>&1; then
  echo "❌ nlp2cmd not found. Install: (cd python && make pip-nlp2cmd)" >&2
  exit 1
fi

export STTS_MOCK_STT=1
export STTS_NLP2CMD_ENABLED=1
export STTS_TTS_NO_PLAY=1

echo "== Debug quoting (dry-run) =="
$PYTHON "$STTS" --stt-file "$SAMPLE" --dry-run nlp2cmd -r --query "{STT}" --auto-confirm

echo "== Wrapper: STT -> nlp2cmd (prints translation) =="
$PYTHON "$STTS" --stt-file "$SAMPLE" nlp2cmd -r --query "{STT}" --auto-confirm

echo "== Alternative: STT -> stdout -> nlp2cmd stdin (robust) =="
$PYTHON "$STTS" --stt-file "$SAMPLE" --stt-once | nlp2cmd -r stdin --auto-confirm
