#!/usr/bin/env bash
# Start Romance of the Three Kingdoms V (san5) under DOSBox on the VNC display.
# Mounts and drive switch are in san5-dosbox.conf [autoexec]; this script runs
# play.bat and sends Enter to skip intro splash screens.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONF="${SCRIPT_DIR}/san5-dosbox.conf"
GAME_DIR="${SAN5_GAME_DIR:-${HOME}/Games/san5}"

# Match x11vnc_start.sh virtual display
export DISPLAY="${SAN5_DISPLAY:-:99}"
unset WAYLAND_DISPLAY

ENTER_COUNT="${SAN5_ENTER_COUNT:-4}"
ENTER_DELAY="${SAN5_ENTER_DELAY:-2}"
DOSBOX_WAIT="${SAN5_DOSBOX_WAIT:-3}"

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

# 1. dosbox with san5-dosbox.conf (autoexec: mount c, mount d cdrom, c:)
# 5. -c play  →  runs PLAY.BAT → san586.com
dosbox -conf "$CONF" -c "play" &
DOSBOX_PID=$!

echo "DOSBox PID ${DOSBOX_PID}; waiting ${DOSBOX_WAIT}s for shell..."
sleep "$DOSBOX_WAIT"

if focus_dosbox; then
  echo "Sending Enter to bypass flash screens..."
  send_enter_keys
else
  echo "warning: could not find DOSBox window; splash Enter may need manual keypress" >&2
fi

# Optional: capture mouse + dismiss first dialog (message box OK)
if [[ "${SAN5_GRAB_MOUSE:-0}" == 1 ]]; then
  sleep 1
  if [[ -n "${SAN5_DISMISS_DIALOG:-}" ]]; then
    python3 "${SCRIPT_DIR}/dosbox_mouse.py" -a dismiss || true
  else
    python3 "${SCRIPT_DIR}/dosbox_mouse.py" -a grab || true
  fi
fi

HOST_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
MOUSE="${SCRIPT_DIR}/dosbox_mouse.py"
echo ""
echo "san5 launched. Confirm via VNC:"
echo "  ${HOST_IP:-<host>}:5999  (display ${DISPLAY})"
echo "Mouse:  python3 ${MOUSE} -a move -p 500 200"
echo "Click:  python3 ${MOUSE} -a click -p 500 200   (or: move, then -a grab)"
echo "Stuck:  python3 ${MOUSE} -a release"
echo "Debug:  python3 ${MOUSE} -a debug -v"
echo "Stop DOSBox: kill ${DOSBOX_PID}"
