#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SAMPLES_DIR="$ROOT_DIR/samples"

mkdir -p "$SAMPLES_DIR"

if ! command -v espeak >/dev/null 2>&1; then
  echo "❌ espeak not found. Install: sudo apt install espeak" >&2
  exit 1
fi

# Generate WAV samples (speech)
# Note: for docker tests we also store expected transcript in sidecar .txt

gen() {
  local name="$1"
  local text="$2"
  local wav="$SAMPLES_DIR/$name.wav"

  echo "Generating $wav"
  espeak -v pl -s 160 -w "$wav" "$text" >/dev/null 2>&1 || true
  printf "%s" "$text" > "$wav.txt"
}

gen "cmd_echo_hello" "echo hello"
gen "cmd_ls" "ls"
gen "cmd_make_build" "make build"

echo "✅ Samples generated in: $SAMPLES_DIR"
