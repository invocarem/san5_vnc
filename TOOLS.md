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

`dosbox`, `xdotool`, `Xvfb`, `x11vnc`, `xsetroot`, `xdpyinfo`, `scrot`, Python 3 (stdlib for mouse scripts)

## Optional env (launch / mouse)

- `SAN5_GRAB_MOUSE=1` — auto click or dismiss after `san5_start.sh` (if `SAN5_MOUSE_SYNC=0`)
- `SAN5_DISMISS_DIALOG=1` — with `SAN5_GRAB_MOUSE`, run dismiss instead of click only
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
| First 確認 click | end of `san5_start.sh` (`SAN5_MOUSE_SYNC=1`, default) |
| Click | `dosbox_mouse.py -a move/debug/click` (see `dosbox-mouse` skill) |

Vision: read the PNG in-process when the agent supports images. Otherwise use `skills/minicpm-vision`:

```bash
./skills/minicpm-vision/scripts/san5_look.sh   # capture + JSON with recommended_click
```

Coordinates are 1024×768 from origin (0,0). Script auto-parses pixel coords and retries if the model returns fractions only.

## ModelBest (MiniCPM-V, no native vision)

| Item | Value |
|------|-------|
| API base | `https://api.modelbest.cn/v1` |
| Model | `MiniCPM-V-4.6-Instruct` |
| Public trial key | `sk-pQ8L2zF3XmR5kY9wV4jB7hN1tC6vM0xG3aD5sH2bJ9lK4cZ8` (see [api.md](https://github.com/OpenBMB/MiniCPM-V/blob/main/docs/api.md)) |
| Analyze | `./skills/minicpm-vision/scripts/san5_look.sh` (or `--capture --json`) |
