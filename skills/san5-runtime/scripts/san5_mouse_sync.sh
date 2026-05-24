#!/usr/bin/env bash
# Handle the first SAN5 confirmation dialog mouse sync only.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
MOUSE_SCRIPT="${SAN5_MOUSE_SCRIPT:-${WORKSPACE_ROOT}/skills/dosbox-mouse/scripts/dosbox_mouse.py}"
DISPLAY="${SAN5_DISPLAY:-:99}"
WAIT_SECONDS="${SAN5_MOUSE_SYNC_DELAY:-3}"
SETTLE_SEC="${SAN5_SETTLE_SEC:-0.2}"

export DISPLAY
unset WAYLAND_DISPLAY

if ! xdpyinfo -display "$DISPLAY" >/dev/null 2>&1; then
  echo "error: display ${DISPLAY} unavailable; start runtime first" >&2
  exit 1
fi

if [[ "${SAN5_MOUSE_SYNC:-1}" == 1 ]]; then
  cap_x="${SAN5_CAPTURE_X:-512}"
  cap_y="${SAN5_CAPTURE_Y:-384}"
  x1="${SAN5_CONFIRM_X1:-432}"
  y1="${SAN5_CONFIRM_Y1:-398}"
  x2="${SAN5_CONFIRM_X2:-592}"
  y2="${SAN5_CONFIRM_Y2:-422}"
  cx=$(( (x1 + x2) / 2 ))
  cy=$(( (y1 + y2) / 2 ))

  echo "Waiting ${WAIT_SECONDS}s for first confirmation dialog..."
  sleep "$WAIT_SECONDS"
  echo "first-dialog: move --sync → click → move --sync → debug -v → click"
  python3 "$MOUSE_SCRIPT" -a move -p "$cap_x" "$cap_y" --sync || true
  python3 "$MOUSE_SCRIPT" -a click || true
  sleep 0.3
  python3 "$MOUSE_SCRIPT" -a move -p "$cx" "$cy" --sync || true
  sleep "$SETTLE_SEC"
  python3 "$MOUSE_SCRIPT" -a debug -v || true
  python3 "$MOUSE_SCRIPT" -a click || true
  exit 0
fi

if [[ "${SAN5_GRAB_MOUSE:-0}" == 1 ]]; then
  sleep 1
  if [[ -n "${SAN5_DISMISS_DIALOG:-}" ]]; then
    python3 "${MOUSE_SCRIPT}" -a dismiss || true
  else
    python3 "${MOUSE_SCRIPT}" -a click || true
  fi
fi
