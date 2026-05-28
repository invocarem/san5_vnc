#!/usr/bin/env bash
# Start Romance of the Three Kingdoms V (san5) under DOSBox on the VNC display.
# Mounts and drive switch are in san5-dosbox.conf [autoexec]; this script runs
# play.bat and sends Enter to skip intro splash screens.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
X11VNC_SCRIPT="${WORKSPACE_ROOT}/skills/san5-x11vnc/scripts/x11vnc_start.sh"
CONF="${SCRIPT_DIR}/san5-dosbox.conf"
MOUSE_SCRIPT="${SAN5_MOUSE_SCRIPT:-${WORKSPACE_ROOT}/skills/mouse/scripts/san5_mouse.py}"
GAME_DIR="${SAN5_GAME_DIR:-${HOME}/Games/san5}"

export DISPLAY="${SAN5_DISPLAY:-:99}"
unset WAYLAND_DISPLAY

ENTER_COUNT="${SAN5_ENTER_COUNT:-4}"
ENTER_DELAY="${SAN5_ENTER_DELAY:-2}"
DOSBOX_WAIT="${SAN5_DOSBOX_WAIT:-3}"
SAN5_SCREEN_WIDTH="${SAN5_SCREEN_WIDTH:-1024}"
SAN5_SCREEN_HEIGHT="${SAN5_SCREEN_HEIGHT:-768}"
SAN5_WINDOW_X="${SAN5_WINDOW_X:-0}"
SAN5_WINDOW_Y="${SAN5_WINDOW_Y:-0}"
SAN5_FORCE_WINDOW_SIZE="${SAN5_FORCE_WINDOW_SIZE:-1}"

ensure_vnc() {
  if xdpyinfo -display "$DISPLAY" >/dev/null 2>&1; then
    return 0
  fi
  echo "Display ${DISPLAY} not ready; starting VNC environment..."
  "${X11VNC_SCRIPT}"
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
  if [[ "$SAN5_FORCE_WINDOW_SIZE" == 1 ]]; then
    xdotool windowsize "$win" "$SAN5_SCREEN_WIDTH" "$SAN5_SCREEN_HEIGHT" 2>/dev/null || true
  fi
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

dosbox -conf "$CONF" \
 -c "play" &
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

HOST_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
MOUSE="${MOUSE_SCRIPT}"
echo ""
echo "san5 launched. Confirm via VNC:"
echo "  ${HOST_IP:-<host>}:5999  (display ${DISPLAY})"
echo ""
echo "First CD/確認 dialog: see skills/san5-ui/SKILL.md (first_cd_confirm)"
echo "Mouse:  python3 ${MOUSE} -a move -p X Y --sync"
echo "Click:  python3 ${MOUSE} -a debug -v && python3 ${MOUSE} -a click"
echo "Stuck:  python3 ${MOUSE} -a release"
echo "Stop DOSBox: kill ${DOSBOX_PID}"
