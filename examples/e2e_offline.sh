#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "== Python offline E2E =="
STTS_MOCK_STT=1 bash "$ROOT/python/tests/docker_test.sh"

echo "== Node.js offline E2E =="
STTS_MOCK_STT=1 bash "$ROOT/nodejs/tests/docker_test.sh"

echo "✅ offline e2e ok"
