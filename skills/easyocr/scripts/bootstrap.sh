#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

echo "[san5] easyocr: syncing uv group 'easyocr'..." >&2
exec uv sync --group easyocr
