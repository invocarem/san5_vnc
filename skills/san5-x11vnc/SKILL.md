---
name: san5-x11vnc
description: >-
  Start the san5 virtual display (Xvfb :99) and x11vnc server on port 5999 for
  remote viewing. Use when VNC is down, display :99 is unavailable, or when
  intentionally resetting the display stack before play.
---

# san5 x11vnc (virtual display + VNC)

Script: `skills/san5-x11vnc/scripts/x11vnc_start.sh`

Run from workspace root or use full paths.

## Start (once per session)

```bash
./skills/san5-x11vnc/scripts/x11vnc_start.sh
```

Creates display `:99` at **1024×768**, VNC on port **5999**. Connect via `<host-ip>:5999` (see `TOOLS.md`).

`san5_start.sh` calls this automatically if `:99` is not ready — you only need to run it manually when starting the display without launching the game.

## Behavior

- Kills existing `Xvfb` / `x11vnc` before restart (destructive — run only when intentional)
- Hides the X11 pointer on `:99` so only the in-game cursor shows in VNC
- x11vnc flags: `-noxfixes -nocursor -nocursorshape -nocursorpos` (single cursor in stream)

If the VNC client still shows two cursors, disable **local cursor** in the viewer (TigerVNC, RealVNC, Remmina — see script output).

## Environment

| Variable | Default | Meaning |
|----------|---------|---------|
| `SAN5_SCREEN_WIDTH` / `SAN5_SCREEN_HEIGHT` | `1024` / `768` | Xvfb resolution |

Display is always `:99`; override connect details in `TOOLS.md` (`SAN5_DISPLAY`).

## Safety

- Do not `pkill -9 x11vnc` or `pkill -9 Xvfb` without asking the user
- Prefer checking `xdpyinfo -display :99` before restarting — avoid nuking a working display

## Stop

```bash
pkill -9 x11vnc Xvfb   # tears down display + VNC — ask user first
```

Game process (DOSBox) is separate — see `san5-starter`.
