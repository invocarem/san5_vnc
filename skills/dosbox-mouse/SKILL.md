---
name: dosbox-mouse
description: >-
  Move and click inside the DOSBox san5 window on the VNC display using
  window-relative coordinates (typically 800×600). Use for mouse control,
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

1. Move to target: `-a move -p X Y`
2. Click: `-a click -p X Y` or move then `-a grab`
3. If stuck after release, `-a grab` again before more clicks

## Environment

| Variable | Default | Meaning |
|----------|---------|---------|
| `SAN5_DISPLAY` | `:99` | X11 display |
| `SAN5_LOGICAL_WIDTH` / `SAN5_LOGICAL_HEIGHT` | `800` / `600` | For `--scale` |
| `SAN5_WAKE_CURSOR` | `1` | Pointer jiggle after move |

Full list and troubleshooting: workspace `README.md`.
