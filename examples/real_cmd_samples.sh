#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SAMPLES_DIR="$ROOT/python/samples"

DUR_SECONDS="${STTS_REAL_SAMPLE_SECONDS:-5}"
DEVICE="${STTS_REC_DEVICE:-}"

mkdir -p "$SAMPLES_DIR"

slugify() {
  echo "$1" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/_/g; s/^_+//; s/_+$//'
}

record_one() {
  local prompt="$1"
  local slug
  slug="$(slugify "$prompt")"
  local wav="$SAMPLES_DIR/real_${slug}.wav"

  echo ""
  echo "== Record sample =="
  echo "Speak (exactly): $prompt"
  echo "Recording: ${DUR_SECONDS}s -> $wav"

  if [ -n "$DEVICE" ]; then
    arecord -D "$DEVICE" -d "$DUR_SECONDS" -f S16_LE -r 16000 -c 1 -t wav "$wav" >/dev/null 2>&1 || true
  else
    arecord -d "$DUR_SECONDS" -f S16_LE -r 16000 -c 1 -t wav "$wav" >/dev/null 2>&1 || true
  fi

  if [ ! -f "$wav" ]; then
    echo "❌ Recording failed: $wav" >&2
    return 1
  fi

  printf "%s" "$prompt" > "$wav.txt"
  echo "✅ Saved: $wav (+ .txt)"
}

COMMANDS=(
  "git status"
  "docker ps"
  "ls"
  "make build"
  "echo hello"
)

for cmd in "${COMMANDS[@]}"; do
  record_one "$cmd"
done

echo ""
echo "All samples recorded in: $SAMPLES_DIR"
echo "Run benchmark on real samples:"
echo "  ./examples/benchmark.sh $SAMPLES_DIR/real_*.wav"
