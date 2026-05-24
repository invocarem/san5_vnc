#!/usr/bin/env bash
# Capture + analyze san5 screen with visible progress. Prints JSON to stdout.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

IMAGE="${1:-san5_screenshot.png}"

echo "[san5] look: debug cursor → capture → analyze (MiniCPM-V, typically 20–60s)…" >&2
exec python3 skills/minicpm-vision/scripts/analyze_screenshot.py --capture --json "$IMAGE"
