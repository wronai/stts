#!/usr/bin/env bash
# Example: stts daemon + nlp2cmd service
# Wake-word: "hejken" (Polish: hey Ken)
#
# Usage:
#   1. Start nlp2cmd service (Terminal 1):
#      cd /home/tom/github/wronai/nlp2cmd
#      nlp2cmd service --host 0.0.0.0 --port 8008
#
#   2. Start stts daemon (Terminal 2):
#      bash examples/daemon_nlp2cmd.sh
#
#   3. Say: "hejken lista folderów" or "hejken pokaż procesy"
#
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STTS="$ROOT/python/stts"
VENV_PY="$ROOT/venv/bin/python"

if [ -f "$VENV_PY" ]; then
  PYTHON="$VENV_PY"
else
  PYTHON="python3"
fi

# Configuration
NLP2CMD_URL="${STTS_NLP2CMD_URL:-http://localhost:8008}"
LOG_FILE="${STTS_DAEMON_LOG:-}"

# Recommended offline STT settings (whisper.cpp)
STT_PROVIDER="${STTS_DAEMON_STT_PROVIDER:-whisper_cpp}"
STT_MODEL="${STTS_DAEMON_STT_MODEL:-medium}"

echo "=============================================="
echo "  STTS Daemon Mode + nlp2cmd Service"
echo "=============================================="
echo ""
echo "nlp2cmd URL: $NLP2CMD_URL"
echo "Wake-word:   hejken / heyken / hey ken"
echo "STT:         ${STT_PROVIDER} (${STT_MODEL})"
echo ""
echo "Examples:"
echo "  'hejken lista folderów'"
echo "  'hejken pokaż wszystkie procesy'"
echo "  'hejken uruchom docker'"
echo ""
echo "Press Ctrl+C to stop."
echo ""

# Check if nlp2cmd service is running
if ! curl -s "${NLP2CMD_URL}/health" >/dev/null 2>&1; then
  echo "⚠️  Warning: nlp2cmd service not responding at $NLP2CMD_URL"
  echo "   Start it with: nlp2cmd service --host 0.0.0.0 --port 8008"
  echo ""
fi

# Run daemon
DAEMON_ARGS=(--daemon --nlp2cmd-url "$NLP2CMD_URL" --stt-provider "$STT_PROVIDER" --stt-model "$STT_MODEL")

if [ -n "$LOG_FILE" ]; then
  DAEMON_ARGS+=(--daemon-log "$LOG_FILE")
fi

exec $PYTHON "$STTS" "${DAEMON_ARGS[@]}"
