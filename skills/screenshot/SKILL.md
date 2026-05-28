---
name: screenshot
description: >-
  Capture the san5 framebuffer with scrot on the VNC display. Use before OCR,
  native vision, or when verifying game state from pixels.
---

# san5 screenshot

Capture with **`scrot`** on display `:99`. Full **1024×768** framebuffer (DOSBox at 0,0). PNG pixels match `san5_mouse.py -p X Y`.

Framebuffer capture lives **only** in this skill — `easyocr` reads the PNG; it does not run `scrot`.

Script: **`scripts/san5_capture.py`** only.

## Quick start

From workspace root:

```bash
./skills/screenshot/scripts/san5_capture.py
# → screenshots/run1/001.png (SAN5_RUN unset → run1)
# → screenshots/latest.png (refreshed for OCR / vision)

./skills/screenshot/scripts/san5_capture.py
# → screenshots/run1/002.png

SAN5_RUN=run2 ./skills/screenshot/scripts/san5_capture.py
# → screenshots/run2/001.png

./skills/screenshot/scripts/san5_capture.py --new-run
# next run folder (run2, run3, …) and 001.png
```

## Run layout

All under `screenshots/` (gitignored):

| Path | Role |
|------|------|
| `run1/001.png`, `run1/002.png`, … | Frames when `SAN5_RUN` is unset or `run1` |
| `run2/001.png`, … | Set `SAN5_RUN=run2` or use `--new-run` |
| `latest.png` | Copy of the most recent capture (default for OCR) |

If **`SAN5_RUN` is not set**, captures go to **`run1`**. Sequence numbers are per run folder (3 digits). Each capture picks the next `NNN.png` in that folder.

Custom path (bypasses run layout; does not update `latest.png`):

```bash
./skills/screenshot/scripts/san5_capture.py screenshots/archive/menu.png
```

Manual `scrot` (same behavior):

```bash
scrot -D :99 -a 0,0,1024,768 screenshots/latest.png
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
| `SAN5_SCREENSHOTS_DIR` | `screenshots` | Base directory for runs and `latest.png` |
| `SAN5_RUN` | `run1` | Run folder name (`run1`, `run2`, …) |
| `SAN5_SCREENSHOT` | `screenshots/latest.png` | OCR default path; capture still writes run `NNN.png` + copies here |
| `SAN5_DISPLAY` | `:99` | Pass to `scrot -D` |
| `SAN5_SCREEN_WIDTH` / `SAN5_SCREEN_HEIGHT` | `1024` / `768` | Region for `-a 0,0,W,H` |

## Next step

- **OCR:** `uv run --group easyocr python skills/easyocr/scripts/san5_ocr.py --json` (capture + OCR; reads `latest.png` by default)
- **OCR only:** `san5_ocr.py --no-capture --json` after capture
- **Click:** `skills/mouse` (move → debug → click)
