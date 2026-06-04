#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

echo "[san5] san5-vl-ground: syncing uv group 'san5-vl-ground'..." >&2
exec uv sync --group san5-vl-ground
