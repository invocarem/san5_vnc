# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OpenClaw workspace that runs **Romance of the Three Kingdoms V (san5)** in DOSBox on a virtual display (`:99`), viewable and controllable over **VNC** (port `5999`). The agent plays the game by capturing screenshots, analyzing them with vision, and clicking targets via `dosbox_mouse.py`.

## Key Files

| File | Purpose |
|------|---------|
| `AGENTS.md` | Agent workflow, safety rules, memory organization |
| `TOOLS.md` | Machine-specific values (paths, ports, env vars) — read before running tools |
| `README.md` | CLI quick-start, troubleshooting |
| `MEMORY.md` | Long-term game coordinate/strategy memory (curated, one-line index) |
| `IDENTITY.md` | Agent persona ("Nimis") |
| `SOUL.md` | Agent behavioral principles |

## Directory Structure

```
skills/
├── san5-runtime/          # VNC + DOSBox lifecycle
│   └── scripts/
│       ├── x11vnc_start.sh     # Start Xvfb :99 + x11vnc :5999
│       ├── san5_start.sh       # Launch DOSBox, mount game, send Enter splashes
│       └── san5-dosbox.conf    # DOSBox config (1024x768, autolock=false)
├── dosbox-mouse/           # Pointer control
│   └── scripts/
│       └── dosbox_mouse.py     # move/click/release inside DOSBox
├── screenshot/             # Framebuffer capture
│   └── SKILL.md
├── minicpm-vision/         # Vision API fallback (when agent has no native vision)
│   └── scripts/
│       └── analyze_screenshot.py
```

## Common Commands

All commands run from workspace root (`~/.openclaw/workspace`).

### Runtime

```bash
# Start VNC display (once per session)
./skills/san5-runtime/scripts/x11vnc_start.sh

# Launch DOSBox + san5 game
./skills/san5-runtime/scripts/san5_start.sh

# Stop everything
pkill -f 'dosbox.*san5-dosbox'
pkill -9 x11vnc Xvfb    # tears down VNC — ask user first
```

### Mouse Control

```bash
python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a move   -p X Y [--sync]
python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a debug  [-v]
python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a click
python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a rclick
python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a release
python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a dismiss
```

Sync (`move --sync`), capture (`click`), and release (`release`) are different — see `skills/dosbox-mouse/SKILL.md` (**Concepts**).

### Screenshot

```bash
scrot -D :99 -a 0,0,1024,768 san5_screenshot.png
export DISPLAY=:99
xdotool search --name DOSBox
```

### Vision-driven play

```bash
# Analyze (native vision on PNG, or minicpm-vision --capture)
# Then click with verify:
python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a move -p CX CY --sync
sleep 0.2
python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a debug -v
python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a click

# First dialog (mouse not captured yet): move --sync → click → move --sync → debug -v → click
python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a move -p 512 384 --sync
python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a click
python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a move -p 512 410 --sync
python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a debug -v
python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a click
```

### Vision API (fallback, no native vision)

```bash
export MODELBEST_API_KEY="sk-pQ8L2zF3XmR5kY9wV4jB7hN1tC6vM0xG3aD5sH2bJ9lK4cZ8"
./skills/minicpm-vision/scripts/san5_look.sh
# → JSON with recommended_click.click for dosbox_mouse
```

Agent must announce progress before/after (20–60s API); see `AGENTS.md` Visibility section.

## Architecture

- **Display stack**: Xvfb (`:99`, 1024×768) → x11vnc (port 5999, no local cursor) → VNC viewer
- **DOSBox window**: Always pinned at `(0,0)` with `1024×768` resolution, `autolock=false`
- **Coordinate system**: All positions are window-relative `(x, y)` with origin top-left, matching PNG pixel space
- **Mouse capture**: DOSBox `autolock=false` means the first click inside the window must capture the pointer before subsequent clicks register. This is handled by `san5_start.sh` (mouse sync on first 確認 dialog)
- **No game files in repo**: Game data lives at `~/Games/san5` (`SAN5_GAME_DIR`), not tracked in git

## Safety Rules

- Never `pkill -9 x11vnc` or `Xvfb` without asking the user
- Confirm DOSBox is running before any click sequence
- Run `dosbox_mouse.py -a debug` before long coordinate chains
- Always tie click coordinates to a visible bounding box from the current screenshot
- On `release`, re-capture (`-a click` after `move`) before more clicks

## Env Variables (all optional)

| Variable | Default | Used By |
|----------|---------|---------|
| `SAN5_DISPLAY` | `:99` | All scripts |
| `SAN5_SCREEN_WIDTH/HEIGHT` | `1024` / `768` | Screenshot, launch |
| `SAN5_GAME_DIR` | `~/Games/san5` | san5_start.sh |
| `SAN5_GRAB_MOUSE` | unset | Legacy: run click after launch if `SAN5_MOUSE_SYNC=0` |
| `SAN5_DISMISS_DIALOG` | unset | Dismiss confirm dialog at launch |
| `SAN5_MOUSE_SYNC` | `1` | Auto mouse sync on first dialog |
| `SAN5_ENTER_COUNT/DELAY` | `4` / `2` | Splash Enter keypresses |
| `MODELBEST_API_KEY` | — | Vision API auth |
