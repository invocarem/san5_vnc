---
name: screenshot
description: >-
  Capture the DOSBox san5 game framebuffer from the VNC display for vision
  analysis. Use before vision-click, when describing game state from pixels,
  or when the user asks for a screenshot of san5.
---

# san5 screenshot

Script: `skills/screenshot/scripts/san5_capture.sh`

Crops to the **DOSBox window** only. Pixel coordinates in the PNG match **window-relative** coords used by `dosbox_mouse.py -p X Y` (typically 800×600).

## Capture

```bash
./skills/screenshot/scripts/san5_capture.sh
./skills/screenshot/scripts/san5_capture.sh /tmp/san5.png
```

Output (stdout) includes `path=`, `width`/`height` (xdotool), `image_width`/`image_height` (PNG), and screen offset (`screen_x`, `screen_y`).

If `image_height` < `height`, vision bboxes are in PNG space — scale before click:  
`y_click = round(y * height / image_height)` (same for X if widths differ).

## Prerequisites

- `scrot`, `xdotool`
- Display `:99` up, DOSBox running (`san5-runtime`, `TOOLS.md`)

## Environment

| Variable | Default | Meaning |
|----------|---------|---------|
| `SAN5_DISPLAY` | `:99` | X11 display |

## Manual capture (full root)

Only if debugging layout; vision-click should use the script above:

```bash
scrot -D :99 /tmp/full.png
```

## Next step

Read the PNG with vision, then follow `skills/vision-click/SKILL.md` to click targets.
