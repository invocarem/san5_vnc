#!/usr/bin/env bash
# Start Romance of the Three Kingdoms V (san5) under DOSBox on the VNC display.
# Mounts and drive switch are in san5-dosbox.conf [autoexec]; this script runs
# play.bat and sends Enter to skip intro splash screens.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
CONF="${SCRIPT_DIR}/san5-dosbox.conf"
MOUSE_SCRIPT="${SAN5_MOUSE_SCRIPT:-${WORKSPACE_ROOT}/skills/dosbox-mouse/scripts/dosbox_mouse.py}"
CLICK_TARGET="${SAN5_CLICK_TARGET:-${WORKSPACE_ROOT}/skills/vision-click/scripts/click_target.py}"
GAME_DIR="${SAN5_GAME_DIR:-${HOME}/Games/san5}"

# Match x11vnc_start.sh virtual display
export DISPLAY="${SAN5_DISPLAY:-:99}"
unset WAYLAND_DISPLAY

ENTER_COUNT="${SAN5_ENTER_COUNT:-4}"
ENTER_DELAY="${SAN5_ENTER_DELAY:-2}"
DOSBOX_WAIT="${SAN5_DOSBOX_WAIT:-3}"
SAN5_SCREEN_WIDTH="${SAN5_SCREEN_WIDTH:-1024}"
SAN5_SCREEN_HEIGHT="${SAN5_SCREEN_HEIGHT:-768}"
SAN5_WINDOW_X="${SAN5_WINDOW_X:-0}"
SAN5_WINDOW_Y="${SAN5_WINDOW_Y:-0}"

ensure_vnc() {
  if xdpyinfo -display "$DISPLAY" >/dev/null 2>&1; then
    return 0
  fi
  echo "Display ${DISPLAY} not ready; starting VNC environment..."
  "${SCRIPT_DIR}/x11vnc_start.sh"
  export DISPLAY=:99
  sleep 1
  if ! xdpyinfo -display "$DISPLAY" >/dev/null 2>&1; then
    echo "error: display ${DISPLAY} still unavailable" >&2
    exit 1
  fi
}

focus_dosbox() {
  local win=""
  for _ in $(seq 1 40); do
    win="$(xdotool search --name 'DOSBox' 2>/dev/null | head -1 || true)"
    if [[ -n "$win" ]]; then
      xdotool windowactivate --sync "$win" 2>/dev/null || true
      echo "$win"
      return 0
    fi
    sleep 0.25
  done
  return 1
}

layout_dosbox() {
  local win="$1"
  xdotool windowmove "$win" "$SAN5_WINDOW_X" "$SAN5_WINDOW_Y"
  xdotool windowsize "$win" "$SAN5_SCREEN_WIDTH" "$SAN5_SCREEN_HEIGHT" 2>/dev/null || true
  echo "  DOSBox at (${SAN5_WINDOW_X},${SAN5_WINDOW_Y}) ${SAN5_SCREEN_WIDTH}x${SAN5_SCREEN_HEIGHT}"
}

send_enter_keys() {
  local i
  for ((i = 1; i <= ENTER_COUNT; i++)); do
    sleep "$ENTER_DELAY"
    xdotool key Return 2>/dev/null || true
    echo "  sent Enter (${i}/${ENTER_COUNT})"
  done
}

sync_mouse_first_dialog() {
  # One-time capture → move → grab for 確認 (CD dialog). Later screens: move/click only.
  local wait="${SAN5_MOUSE_SYNC_DELAY:-3}"
  export SAN5_CAPTURE_X="${SAN5_CAPTURE_X:-512}"
  export SAN5_CAPTURE_Y="${SAN5_CAPTURE_Y:-384}"
  local x1="${SAN5_CONFIRM_X1:-432}" y1="${SAN5_CONFIRM_Y1:-398}"
  local x2="${SAN5_CONFIRM_X2:-592}" y2="${SAN5_CONFIRM_Y2:-422}"

  echo "Waiting ${wait}s for 確認 dialog, then mouse sync..."
  sleep "$wait"
  if [[ ! -f "$CLICK_TARGET" ]]; then
    echo "warning: missing ${CLICK_TARGET}; skip mouse sync" >&2
    return 0
  fi
  python3 "$CLICK_TARGET" --bbox "$x1" "$y1" "$x2" "$y2" --first-dialog || true
}

if [[ ! -f "$CONF" ]]; then
  echo "error: missing config ${CONF}" >&2
  exit 1
fi

if [[ ! -d "$GAME_DIR" ]]; then
  echo "error: game directory not found: ${GAME_DIR}" >&2
  exit 1
fi

if [[ ! -f "${GAME_DIR}/PLAY.BAT" && ! -f "${GAME_DIR}/play.bat" ]]; then
  echo "warning: PLAY.BAT not found under ${GAME_DIR}" >&2
fi

ensure_vnc

echo "Starting DOSBox (config: ${CONF})"
echo "  [autoexec] mount c/d, c: — then -c play"

# 1. dosbox with san5-dosbox.conf (autoexec: mount c, mount d cdrom, c:)
# 5. -c play  →  runs PLAY.BAT → san586.com
dosbox -conf "$CONF" -c "play" &
DOSBOX_PID=$!

echo "DOSBox PID ${DOSBOX_PID}; waiting ${DOSBOX_WAIT}s for shell..."
sleep "$DOSBOX_WAIT"

if win="$(focus_dosbox)"; then
  layout_dosbox "$win"
  echo "Sending Enter to bypass flash screens..."
  send_enter_keys
else
  echo "warning: could not find DOSBox window; splash Enter may need manual keypress" >&2
fi

# First 確認 dialog: capture mouse in DOSBox, click button (once per launch)
if [[ "${SAN5_MOUSE_SYNC:-1}" == 1 ]]; then
  sync_mouse_first_dialog
elif [[ "${SAN5_GRAB_MOUSE:-0}" == 1 ]]; then
  sleep 1
  if [[ -n "${SAN5_DISMISS_DIALOG:-}" ]]; then
    python3 "${MOUSE_SCRIPT}" -a dismiss || true
  else
    python3 "${MOUSE_SCRIPT}" -a grab || true
  fi
fi

HOST_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
MOUSE="${MOUSE_SCRIPT}"
echo ""
echo "san5 launched. Confirm via VNC:"
echo "  ${HOST_IP:-<host>}:5999  (display ${DISPLAY})"
echo "Mouse:  python3 ${MOUSE} -a move -p 500 200"
echo "Click:  python3 ${MOUSE} -a click -p 500 200   (or: move, then -a grab)"
echo "Stuck:  python3 ${MOUSE} -a release"
echo "Debug:  python3 ${MOUSE} -a debug -v"
echo "Stop DOSBox: kill ${DOSBOX_PID}"
