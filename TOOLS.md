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

`dosbox`, `xdotool`, `Xvfb`, `x11vnc`, `xsetroot`, `xdpyinfo`, `scrot`, Python 3 (stdlib for mouse scripts), `uv` (for optional local OCR deps)

## Optional env (launch)

- `SAN5_ENTER_COUNT` / `SAN5_ENTER_DELAY` — splash Enter keypresses
- `SAN5_MOUSE_SCRIPT` — override path to `dosbox_mouse.py`

## Screenshot / vision play

| Item | Value |
|------|-------|
| Display | `:99` (`SAN5_DISPLAY`) |
| Screen / window | `1024×768` (`SAN5_SCREEN_WIDTH` / `SAN5_SCREEN_HEIGHT`) |
| DOSBox position | `(0,0)` (`SAN5_WINDOW_X` / `SAN5_WINDOW_Y`) |
| Default capture path | `san5_screenshot.png` (gitignored) |
| Capture | `scrot -D :99 -a 0,0,1024,768 san5_screenshot.png` |
| First 確認 click | `skills/san5-ui/SKILL.md` → **first_cd_confirm** |
| Click | `dosbox_mouse.py -a move/debug/click` (see `dosbox-mouse` skill) |

Vision: read the PNG in-process when the agent supports images. Otherwise use `skills/minicpm-vision`:

```bash
./skills/minicpm-vision/scripts/san5_look.sh   # capture + JSON with recommended_click
```

Coordinates are 1024×768 from origin (0,0). Script auto-parses pixel coords and retries if the model returns fractions only.

## Local OCR (EasyOCR)

| Item | Value |
|------|-------|
| Workspace Python | `uv` project rooted at `~/.openclaw/workspace` |
| Sync deps | `uv sync --group easyocr` |
| Capture + OCR | `./skills/dosbox-easyocr/scripts/san5_ocr.sh` |
| Direct script | `uv run --group easyocr python skills/dosbox-easyocr/scripts/analyze_screenshot.py --capture --json` |
| Match label | `--match 確認` / `--match 開始新遊戲` |
| Languages | `SAN5_EASYOCR_LANGS=ch_tra,en` |
| Min confidence | `SAN5_EASYOCR_MIN_CONFIDENCE=0.5` |

Use OCR for text-heavy dialogs and menus. For non-text UI or when you need a model-picked next action, use `minicpm-vision` instead.

## ModelBest (MiniCPM-V, no native vision)

| Item | Value |
|------|-------|
| API base | `https://api.modelbest.cn/v1` |
| Model | `MiniCPM-V-4.6-Instruct` |
| Public trial key | `sk-pQ8L2zF3XmR5kY9wV4jB7hN1tC6vM0xG3aD5sH2bJ9lK4cZ8` (see [api.md](https://github.com/OpenBMB/MiniCPM-V/blob/main/docs/api.md)) |
| Analyze | `./skills/minicpm-vision/scripts/san5_look.sh` (or `--capture --json`) |
