# TOOLS.md — san5 local setup

Skills describe *how* tools work. This file is *your* machine-specific values.

## VNC

| Item | Value |
|------|-------|
| Display | `:99` (`SAN5_DISPLAY`) |
| VNC port | `5999` |
| Connect | `<host-ip>:5999` — run `hostname -I` on the game host |

Start display: `./skills/san5-x11vnc/scripts/x11vnc_start.sh`

## Game files

| Item | Value |
|------|-------|
| Directory | `~/Games/san5` (`SAN5_GAME_DIR`) |
| Launcher | `PLAY.BAT` / `play.bat` under game dir |

Not stored in git — install ROMs/data locally.

Launch: `./skills/san5-starter/scripts/san5_start.sh`

## Prerequisites

`dosbox`, `xdotool`, `Xvfb`, `x11vnc`, `xsetroot`, `xdpyinfo`, `scrot`, Python 3 (stdlib for mouse scripts), `uv` (for EasyOCR deps)

## Optional env (launch)

- `SAN5_ENTER_COUNT` / `SAN5_ENTER_DELAY` — splash Enter keypresses
- `SAN5_MOUSE_SCRIPT` — override path to `san5_mouse.py`

## Screenshot / vision play

| Item | Value |
|------|-------|
| Display | `:99` (`SAN5_DISPLAY`) |
| Screen / window | `1024×768` (`SAN5_SCREEN_WIDTH` / `SAN5_SCREEN_HEIGHT`) |
| DOSBox position | `(0,0)` (`SAN5_WINDOW_X` / `SAN5_WINDOW_Y`) |
| Default screenshot | `screenshots/latest.png` (`SAN5_SCREENSHOT`, gitignored dir) |
| Run archive | `screenshots/run1/001.png`, … (`SAN5_RUN`, default `run1`) |
| Capture | `python3 skills/screenshot/scripts/san5_capture.py` (`--new-run`, `--run NAME`) |
| First 確認 click | `skills/san5-ui/SKILL.md` → **first_cd_confirm** |
| Click | `san5_mouse.py -a move/debug/click` (see `mouse` skill) |

Coordinates are 1024×768 from origin (0,0). Prefer EasyOCR for text labels; verify every click with `debug -v` before promoting coords to `san5-ui`.

## Local OCR (EasyOCR)

| Item | Value |
|------|-------|
| Workspace Python | `uv` project rooted at `~/.openclaw/workspace` |
| Sync deps | `uv sync --group easyocr` |
| Capture + OCR | `uv run --group easyocr python skills/easyocr/scripts/san5_ocr.py --json` |
| Match label | `…/san5_ocr.py --json --match 確認` |
| OCR only (PNG exists) | `…/san5_ocr.py --no-capture --json` |
| Languages | `SAN5_EASYOCR_LANGS=ch_tra,en` |
| Min confidence | `SAN5_EASYOCR_MIN_CONFIDENCE=0.5` |
| GPU | `SAN5_EASYOCR_GPU=1` to enable |

Use OCR for text-heavy dialogs and menus. For non-text UI, add anchors to `skills/san5-ui/SKILL.md` or use agent native vision on `screenshots/latest.png` when available.
