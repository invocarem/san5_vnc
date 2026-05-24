---
name: san5-runtime
description: >-
  Start the san5 VNC display stack (Xvfb :99, x11vnc port 5999) and launch
  Romance of the Three Kingdoms V in DOSBox. Use when starting or restarting
  the game environment, VNC, or DOSBox for san5.
---

# san5 runtime (VNC + DOSBox)

Scripts live in `skills/san5-runtime/scripts/`. Run from workspace root or use full paths.

## Start VNC (once per session)

```bash
./skills/san5-runtime/scripts/x11vnc_start.sh
```

Creates display `:99`, VNC on port **5999**. See `TOOLS.md` for host/port notes.

## Launch game

```bash
./skills/san5-runtime/scripts/san5_start.sh
```

Optional:

```bash
SAN5_MOUSE_SYNC=0 ./skills/san5-runtime/scripts/san5_start.sh   # skip first 確認 click
SAN5_GRAB_MOUSE=1 ./skills/san5-runtime/scripts/san5_start.sh   # legacy click only (if MOUSE_SYNC=0)
```

`san5_start.sh` calls `x11vnc_start.sh` automatically if display `:99` is down.

By default **`SAN5_MOUSE_SYNC=1`**: after splash Enter keys, waits for the CD/確認 dialog, then move→click (capture)→move→debug→click (one-time). Later screens use move → debug → click.

Display and DOSBox window are **1024×768** at **(0, 0)**. Override: `SAN5_SCREEN_WIDTH`, `SAN5_CONFIRM_X1`…`Y2`, `SAN5_CAPTURE_X`/`Y`, `SAN5_MOUSE_SYNC_DELAY` (default 3s).

## Config

- `scripts/san5-dosbox.conf` — mounts, 1024×768 window at (0,0), `autolock=false`
- Game files: `SAN5_GAME_DIR` (default in `TOOLS.md`), not in this repo

## Safety

- Do not `pkill -9 x11vnc` or `pkill -9 Xvfb` without asking the user
- `x11vnc_start.sh` kills existing Xvfb/x11vnc before restart — only run when intentional

## Stop

```bash
pkill -f 'dosbox.*san5-dosbox'
pkill -9 x11vnc Xvfb   # only when tearing down the whole stack
```
