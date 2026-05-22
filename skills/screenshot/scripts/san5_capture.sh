#!/usr/bin/env bash
# Capture the DOSBox san5 window on the VNC display (window-relative coords match dosbox_mouse -p).
set -euo pipefail

DISPLAY="${SAN5_DISPLAY:-:99}"
OUT="${1:-san5_screenshot.png}"

export DISPLAY
unset WAYLAND_DISPLAY

win="$(xdotool search --name DOSBox 2>/dev/null | head -1)"
if [[ -z "$win" ]]; then
  echo "error: DOSBox window not found on $DISPLAY" >&2
  echo "  start VNC + game first (san5-runtime)" >&2
  exit 1
fi

eval "$(xdotool getwindowgeometry --shell "$win")"

# scrot -a: X,Y,W,H (top-left + size)
scrot -D "$DISPLAY" -a "${X},${Y},${WIDTH},${HEIGHT}" "$OUT"

img_size="$(file -b "$OUT" | sed -n 's/.* \([0-9]*\) x \([0-9]*\).*/\1 \2/p')"
read -r img_w img_h <<< "${img_size:-$WIDTH $HEIGHT}"

echo "path=$OUT"
echo "display=$DISPLAY"
echo "image_width=${img_w:-$WIDTH}"
echo "image_height=${img_h:-$HEIGHT}"
echo "window=$win"
echo "screen_x=$X"
echo "screen_y=$Y"
echo "width=$WIDTH"
echo "height=$HEIGHT"
