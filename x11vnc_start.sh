#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Kill everything (|| true: ok if not already running — pkill returns 1 with set -e)
pkill -9 Xvfb 2>/dev/null || true
pkill -9 x11vnc 2>/dev/null || true

# Start fresh
Xvfb :99 -screen 0 1024x768x24 &
sleep 2

unset WAYLAND_DISPLAY
export DISPLAY=:99

# Hide black X11 arrow on :99 — only the game cursor (in DOSBox) should be visible
xsetroot -display :99 -cursor_name none

# One cursor in the VNC stream (game draws it in the framebuffer):
#   -noxfixes:      stop XFIXES from forcing "-cursor most"
#   -nocursor:      do not send a separate VNC pointer to the viewer
#   -nocursorshape/-nocursorpos: extra safety for Tight/tiger clients
#   (never use -multiptr — duplicate pointers)
x11vnc -display :99 -forever -shared -nopw \
  -noxfixes -nocursor -nocursorshape -nocursorpos \
  -repeat -noxdamage -rfbport 5999 &

HOST_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
echo "VNC server running on display :99, port 5999"
echo "Connect to: ${HOST_IP:-localhost}:5999"
echo ""
echo "If you STILL see two cursors in the VNC app, disable its LOCAL cursor:"
echo "  TigerVNC:  Options → Input → uncheck 'Show local cursor'"
echo "  RealVNC:   turn off 'Render cursor locally'"
echo "  Remmina:   use 'Remote cursor' mode"
