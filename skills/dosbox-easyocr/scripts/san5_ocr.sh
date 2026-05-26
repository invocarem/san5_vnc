#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

IMAGE="${1:-san5_screenshot.png}"
shift || true

echo "[san5] ocr: capture -> easyocr (local OCR, usually faster than API vision)..." >&2
exec uv run --group easyocr python skills/dosbox-easyocr/scripts/analyze_screenshot.py --capture --json "$IMAGE" "$@"
