# TOOLS.md — san5 local setup

Skills describe *how* tools work. This file is *your* machine-specific values.

## VNC

| Item | Value |
|------|-------|
| Display | `:99` (`SAN5_DISPLAY`) |
| VNC port | `5999` |
| Connect | `<host-ip>:5999` — run `hostname -I` on the game host |

Start: `./skills/san5-runtime/scripts/x11vnc_start.sh`

## Game files

| Item | Value |
|------|-------|
| Directory | `~/Games/san5` (`SAN5_GAME_DIR`) |
| Launcher | `PLAY.BAT` / `play.bat` under game dir |

Not stored in git — install ROMs/data locally.

## Prerequisites

`dosbox`, `xdotool`, `Xvfb`, `x11vnc`, `xsetroot`, `xdpyinfo`, `scrot`, Python 3 (stdlib for mouse/vision-click scripts)

## Optional env (launch / mouse)

- `SAN5_GRAB_MOUSE=1` — auto grab or dismiss after `san5_start.sh`
- `SAN5_DISMISS_DIALOG=1` — with grab, run dismiss instead of grab only
- `SAN5_ENTER_COUNT` / `SAN5_ENTER_DELAY` — splash Enter keypresses
- `SAN5_MOUSE_SCRIPT` — override path to `dosbox_mouse.py`

## Screenshot / vision-click

| Item | Value |
|------|-------|
| Display | `:99` (`SAN5_DISPLAY`) |
| Default capture path | `san5_screenshot.png` (gitignored) |
| Capture | `./skills/screenshot/scripts/san5_capture.sh [path]` |
| Click helper | `python3 skills/vision-click/scripts/click_target.py --bbox …` |

Vision analysis uses the agent multimodal read of the PNG (no external API in-repo). Coordinates are window-relative 800×600 inside the cropped capture.
