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
├── san5-x11vnc/            # Xvfb :99 + x11vnc :5999
│   └── scripts/x11vnc_start.sh
├── san5-starter/           # DOSBox launch
│   └── scripts/
│       ├── san5_start.sh
│       └── san5-dosbox.conf
├── san5-ui/                # Game UI coords (markdown only)
│   └── SKILL.md
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

### Display + launch

```bash
# Start VNC display (once per session)
./skills/san5-x11vnc/scripts/x11vnc_start.sh

# Launch DOSBox + san5 game
./skills/san5-starter/scripts/san5_start.sh

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

# First CD/確認 dialog: see skills/san5-ui/SKILL.md (first_cd_confirm)
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
- **Mouse capture**: DOSBox `autolock=false` means the first click inside the window must capture the pointer before subsequent clicks register. After launch, follow `san5-ui` → **first_cd_confirm**
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
| `SAN5_ENTER_COUNT/DELAY` | `4` / `2` | Splash Enter keypresses |
| `MODELBEST_API_KEY` | — | Vision API auth |
