---
name: san5-starter
description: >-
  Launch Romance of the Three Kingdoms V in DOSBox on the san5 VNC display.
  Use when starting or restarting the game; starts x11vnc automatically if
  display :99 is down.
---

# san5 starter (DOSBox launch)

Script: `skills/san5-starter/scripts/san5_start.sh`

Run from workspace root or use full paths.

## Launch game

```bash
./skills/san5-starter/scripts/san5_start.sh
```

If display `:99` is not ready, `san5_start.sh` calls `skills/san5-x11vnc/scripts/x11vnc_start.sh` automatically.

After launch: connect VNC (`TOOLS.md`), then follow **`san5-ui`** for the first CD/確認 dialog (mouse capture + button click).

## What it does

1. Ensures VNC display `:99` is up (`san5-x11vnc` if needed)
2. Starts DOSBox with `scripts/san5-dosbox.conf` (mounts, 1024×768, `autolock=false`)
3. Runs `play.bat`, sends Enter keypresses to skip splash screens
4. Pins DOSBox window at **(0, 0)** **1024×768**

## Config

- `scripts/san5-dosbox.conf` — DOSBox settings and `[autoexec]` mounts
- Game files: `SAN5_GAME_DIR` (default in `TOOLS.md`), not in this repo

## Environment

| Variable | Default | Meaning |
|----------|---------|---------|
| `SAN5_DISPLAY` | `:99` | X11 display |
| `SAN5_GAME_DIR` | `~/Games/san5` | Game install path |
| `SAN5_SCREEN_WIDTH` / `SAN5_SCREEN_HEIGHT` | `1024` / `768` | Window size |
| `SAN5_WINDOW_X` / `SAN5_WINDOW_Y` | `0` / `0` | DOSBox window position |
| `SAN5_ENTER_COUNT` / `SAN5_ENTER_DELAY` | `4` / `2` | Splash Enter keypresses |
| `SAN5_DOSBOX_WAIT` | `3` | Seconds after DOSBox start before focus |
| `SAN5_MOUSE_SCRIPT` | `dosbox_mouse.py` | Override mouse script path |

## Related skills

| Skill | When |
|-------|------|
| `san5-x11vnc` | Start VNC only (without game) |
| `san5-ui` | Button coords and first-dialog procedure |
| `dosbox-mouse` | move / debug / click mechanics |

## Stop

```bash
pkill -f 'dosbox.*san5-dosbox'
```

Tear down VNC: see `san5-x11vnc` (ask user before `pkill -9 x11vnc Xvfb`).
