# Romance of the Three Kingdoms V (san5) — OpenClaw workspace

Run **san5** in DOSBox on virtual display `:99`, view and control over **VNC** (port **5999**). This directory is a self-contained OpenClaw workspace.

| Root file | Role |
|-----------|------|
| `AGENTS.md` | How the agent plays san5, safety, workflow |
| `TOOLS.md` | Your machine: VNC host, game dir, ports |
| `MEMORY.md` | Curated long-term game notes |
| `skills/` | Executable tools + `SKILL.md` per capability |

## Prerequisites

See `TOOLS.md`. Game files live under `~/Games/san5` (or `SAN5_GAME_DIR`).

## Quick start

```bash
cd ~/.openclaw/workspace/projects/san5

# 1) Virtual display + VNC
./skills/san5-runtime/scripts/x11vnc_start.sh

# 2) Launch game
./skills/san5-runtime/scripts/san5_start.sh

# 3) VNC viewer → <host>:5999

# 4) Mouse (800×600 window coordinates)
python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a move -p 400 323
python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a click -p 400 323
```

Optional on launch:

```bash
SAN5_GRAB_MOUSE=1 ./skills/san5-runtime/scripts/san5_start.sh
SAN5_GRAB_MOUSE=1 SAN5_DISMISS_DIALOG=1 ./skills/san5-runtime/scripts/san5_start.sh
```

## Layout

```
.
├── AGENTS.md
├── TOOLS.md
├── MEMORY.md
├── memory/              # daily logs (YYYY-MM-DD.md)
├── skills/
│   ├── san5-runtime/
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       ├── x11vnc_start.sh
│   │       ├── san5_start.sh
│   │       └── san5-dosbox.conf
│   ├── dosbox-mouse/
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       └── dosbox_mouse.py
│   ├── screenshot/
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       └── san5_capture.sh
│   └── vision-click/
│       ├── SKILL.md
│       └── scripts/
│           └── click_target.py
```

Vision play: capture → read PNG → `click_target.py --bbox …` (see `skills/vision-click/SKILL.md`).

## `dosbox_mouse.py`

Full CLI and env vars are documented in `skills/dosbox-mouse/SKILL.md`.

```bash
python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -h
python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a debug -v
```

## Cursor visibility (VNC)

- `x11vnc_start.sh` hides the X11 pointer; only the in-game cursor shows
- If the VNC client shows two cursors, disable local cursor in the viewer

## Troubleshooting

| Problem | What to try |
|---------|-------------|
| Clicks do nothing | `-a grab` or `-a click`; avoid `-a release` unless stuck |
| Wrong position | `-a debug`; `--scale` if window ≠ 800×600 |
| DOSBox not found | `export SAN5_DISPLAY=:99`; start VNC + game |
| Stuck capture | `-a release`, then grab again or restart DOSBox |

## Stopping

```bash
pkill -f 'dosbox.*san5-dosbox'
pkill -9 x11vnc Xvfb    # tears down VNC stack
```
