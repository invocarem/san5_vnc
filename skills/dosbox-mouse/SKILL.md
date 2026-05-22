---
name: dosbox-mouse
description: >-
  Move and click inside the DOSBox san5 window on the VNC display using
  window-relative coordinates (typically 1024×768). Use for mouse control,
  grab/release capture, splash dismiss, or pointer debug on san5.
---

# DOSBox mouse control

Script: `skills/dosbox-mouse/scripts/dosbox_mouse.py`

Coordinates are **window-relative** (origin top-left of the DOSBox window).

```bash
python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -h

python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a move   -p X Y
python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a click  -p X Y
python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a rclick -p X Y
python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a grab
python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a release
python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a dismiss
python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a debug  [-v]
```

## Workflow

**Normal** (mouse already captured in DOSBox):

1. `-a move -p X Y`
2. `-a click -p X Y` or move then `-a grab`

**First dialog** (確認 / CD prompt — game ignores xdotool until you click inside DOSBox once):

1. `-a click -p CX CY` on dialog body (not the button) — **captures** mouse in DOSBox
2. `-a move -p X Y` — move game cursor to 確認
3. `-a grab` — click at current position (or `-a grab -p X Y`)

Or use vision-click: `click_target.py --bbox … --first-dialog`

After `-a release` (Ctrl+F10), repeat capture before more clicks.

## Environment

| Variable | Default | Meaning |
|----------|---------|---------|
| `SAN5_DISPLAY` | `:99` | X11 display |
| `SAN5_LOGICAL_WIDTH` / `SAN5_LOGICAL_HEIGHT` | `1024` / `768` | For `--scale` |
| `SAN5_WAKE_CURSOR` | `1` | Pointer jiggle after move (window-relative, no slow screen --sync) |
| `SAN5_CLICK_SCREEN_SYNC` | `0` | `1` = old slow screen `mousemove --sync` before click (~15s on Xvfb) |
| `SAN5_CLICK_SCREEN_NUDGE` | `1` | Fast unsynced screen warp before mousedown (disable if clicks miss) |

Full list and troubleshooting: workspace `README.md`.
