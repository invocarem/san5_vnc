# Romance of the Three Kingdoms V (san5) on VNC

Run **san5** in DOSBox on a virtual X11 display (`:99`), view and control it over **VNC** (port **5999**). Mouse and clicks are driven by **`dosbox_mouse.py`** (xdotool).

## Prerequisites

- `dosbox`, `xdotool`, `Xvfb`, `x11vnc`, `xsetroot`, `xdpyinfo`
- Game files under `~/Games/san5` (or set `SAN5_GAME_DIR`)
- Python 3 (stdlib only for `dosbox_mouse.py`)

## Quick start

```bash
cd ~/.openclaw/workspace/projects/san5

# 1) Virtual display + VNC (once per session, or after reboot)
./x11vnc_start.sh

# 2) Launch game (starts DOSBox, skips splash with Enter)
./san5_start.sh

# 3) Connect VNC viewer to <host>:5999

# 4) Mouse / clicks (coordinates are inside the DOSBox window, usually 800×600)
python3 dosbox_mouse.py -a move -p 400 323
python3 dosbox_mouse.py -a grab          # click at current position (capture)
python3 dosbox_mouse.py -a click -p 400 323
```

Optional on launch:

```bash
SAN5_GRAB_MOUSE=1 ./san5_start.sh
SAN5_GRAB_MOUSE=1 SAN5_DISMISS_DIALOG=1 ./san5_start.sh   # center click + Enter for OK dialog
```

## Project layout

| File | Purpose |
|------|---------|
| `x11vnc_start.sh` | Xvfb `:99`, hide X11 pointer, start x11vnc on port 5999 |
| `san5_start.sh` | Start DOSBox with `san5-dosbox.conf`, send Enter for intro |
| `dosbox_mouse.py` | **Main** mouse API: move, click, grab, release, debug |
| `san5-dosbox.conf` | DOSBox config (mounts, 800×600 window, `autolock=false`) |

## `dosbox_mouse.py`

All pointer actions use **window-relative** coordinates (origin top-left of the DOSBox window).

```bash
python3 dosbox_mouse.py -h

# Actions (-a / --action)
python3 dosbox_mouse.py -a move   -p X Y    # move only
python3 dosbox_mouse.py -a click  -p X Y    # move + left-click
python3 dosbox_mouse.py -a rclick -p X Y    # move + right-click
python3 dosbox_mouse.py -a grab             # click at current mouse (after move)
python3 dosbox_mouse.py -a release          # Ctrl+F10 — uncapture stuck mouse
python3 dosbox_mouse.py -a dismiss          # center click + Enter (splash OK)
python3 dosbox_mouse.py -a debug  [-v]      # window geometry + pointer (replaces old diag scripts)
python3 dosbox_mouse.py -a show-cursor       # show X11 arrow on :99 (debug)
python3 dosbox_mouse.py -a hide-cursor       # hide X11 arrow again

# Options
python3 dosbox_mouse.py -a click -p 400 323 -v          # verbose: print each xdotool command
python3 dosbox_mouse.py -a click -p 400 323 --scale     # map from logical 800×600 if window size differs
```

### Typical workflow

1. **Move** to a button or map tile: `-a move -p X Y`
2. **Grab** (left-click at that position so DOSBox accepts input): `-a grab`  
   Or one step: `-a click -p X Y`
3. If the cursor stops responding after `-a release`, run **`-a grab`** again before more clicks.

`grab` / `click` use a small pointer **jiggle** so SDL/DOSBox sees motion events (this is why verbose logs show several `mousemove` lines). Disable with `SAN5_WAKE_CURSOR=0` if needed.

### Environment

| Variable | Default | Meaning |
|----------|---------|---------|
| `SAN5_DISPLAY` | `:99` | X11 display for xdotool / DOSBox |
| `SAN5_GAME_DIR` | `~/Games/san5` | Game directory (used by `san5_start.sh`) |
| `SAN5_LOGICAL_WIDTH` / `SAN5_LOGICAL_HEIGHT` | `800` / `600` | Logical size for `--scale` |
| `SAN5_WAKE_CURSOR` | `1` | Jiggle pointer after move (helps game redraw cursor) |
| `SAN5_CLICK_DELAY_MS` | `50` | Delay before/after mouse button events |
| `SAN5_GRAB_MOUSE` | `0` | If `1`, `san5_start.sh` runs grab/dismiss after launch |
| `SAN5_DISMISS_DIALOG` | unset | If set with `SAN5_GRAB_MOUSE=1`, use `-a dismiss` |

## Cursor visibility (VNC)

You will usually **not** see a black system arrow:

- `x11vnc_start.sh` hides the X11 pointer (`xsetroot -cursor_name none`).
- x11vnc runs with `-nocursor` (no separate VNC pointer overlay).
- Only the **game’s white cursor** (drawn inside DOSBox) appears in the picture.

If you see two cursors in the VNC client, disable **local cursor** in the viewer (TigerVNC, RealVNC, Remmina — hints printed by `x11vnc_start.sh`).

Run `python3 dosbox_mouse.py -a debug` for pointer position and tips.

## `san5-dosbox.conf` notes

- `windowresolution=800x600` — coordinates in `dosbox_mouse.py` match this space when the window is 800×600.
- `autolock=false` — absolute pointer from VNC/xdotool (do not set `true` or the cursor looks stuck).

## Troubleshooting

| Problem | What to try |
|---------|-------------|
| Clicks do nothing | `-a grab` or `-a click -p X Y -v`; avoid `-a release` unless stuck |
| No visible cursor | Normal on `:99`; use `-a debug`; move + grab; check VNC “remote cursor” |
| Wrong click position | `-a debug` for window size; try `--scale` if window ≠ 800×600 |
| DOSBox window not found | `export SAN5_DISPLAY=:99`; ensure `./x11vnc_start.sh` and DOSBox are running |
| Stuck capture | `python3 dosbox_mouse.py -a release` then restart DOSBox or grab again |

## Stopping

```bash
pkill -f 'dosbox.*san5-dosbox'    # stop game
# Or use PID printed by san5_start.sh

pkill -9 x11vnc Xvfb              # stop VNC stack (x11vnc_start.sh restarts clean)
```
