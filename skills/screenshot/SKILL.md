---
name: screenshot
description: >-
  Capture the san5 framebuffer with scrot on the VNC display for vision
  analysis. Use before vision-driven clicks, when describing game state from pixels,
  or when the user asks for a screenshot of san5.
---

# san5 screenshot

Capture with **`scrot`** on display `:99`. Full **1024×768** framebuffer (DOSBox at 0,0). PNG pixels match `dosbox_mouse.py -p X Y`.

## Capture

From workspace root:

```bash
scrot -D :99 -a 0,0,1024,768 san5_screenshot.png
```

Custom path or size:

```bash
scrot -D :99 -a 0,0,1024,768 /tmp/san5.png
# SAN5_SCREEN_WIDTH / SAN5_SCREEN_HEIGHT if you changed Xvfb size
```

Use **`-D`** for display (not `-display` — scrot treats `-d` as delay and errors).

## Prerequisites

- `scrot`
- Display `:99` up, DOSBox running (`san5-x11vnc`, `san5-starter`, `TOOLS.md`)

Optional check before capture:

```bash
xdotool search --name DOSBox
```

## Environment

| Variable | Default | Meaning |
|----------|---------|---------|
| `SAN5_DISPLAY` | `:99` | Pass to `scrot -D` |
| `SAN5_SCREEN_WIDTH` / `SAN5_SCREEN_HEIGHT` | `1024` / `768` | Region for `-a 0,0,W,H` |

## Next step

Read the PNG with vision, or run `skills/minicpm-vision` if the agent cannot see images. Then use `skills/dosbox-mouse` (move → debug → click).
