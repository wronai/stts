#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"

CACHE_DIR_PYTHON="${CACHE_DIR_PYTHON:-${HOME}/.config/stts-python}"
CACHE_DIR_NODEJS="${CACHE_DIR_NODEJS:-${HOME}/.config/stts-nodejs}"

usage() {
  cat <<EOF
Usage:
  $0 [--cache-python DIR] [--cache-nodejs DIR]

Env overrides:
  CACHE_DIR_PYTHON
  CACHE_DIR_NODEJS
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --cache-python)
      CACHE_DIR_PYTHON="$2"; shift 2;;
    --cache-nodejs|--cache-node)
      CACHE_DIR_NODEJS="$2"; shift 2;;
    -h|--help)
      usage; exit 0;;
    *)
      echo "Unknown arg: $1" >&2
      usage
      exit 2
      ;;
  esac
done

echo "== stts docker tests =="
echo "CACHE_DIR_PYTHON=$CACHE_DIR_PYTHON"
echo "CACHE_DIR_NODEJS=$CACHE_DIR_NODEJS"

a=0
(
  set +e
  make -C "$ROOT" test-docker CACHE_DIR_PYTHON="$CACHE_DIR_PYTHON" CACHE_DIR_NODEJS="$CACHE_DIR_NODEJS"
  a=$?
  exit $a
)
