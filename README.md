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

Local OCR tooling is managed with `uv` from the workspace root:

```bash
uv sync --group easyocr
```

## Quick start

```bash
cd ~/.openclaw/workspace

# 1) Virtual display + VNC
./skills/san5-x11vnc/scripts/x11vnc_start.sh

# 2) Launch game
./skills/san5-starter/scripts/san5_start.sh

# 3) VNC viewer → <host>:5999

# 4) First CD/確認 dialog — coords in skills/san5-ui/SKILL.md
# 5) Mouse (1024×768 window coordinates)
python3 skills/mouse/scripts/san5_mouse.py -a move -p 400 323 --sync
python3 skills/mouse/scripts/san5_mouse.py -a debug -v
python3 skills/mouse/scripts/san5_mouse.py -a click
```

## Layout

```
.
├── AGENTS.md
├── TOOLS.md
├── MEMORY.md
├── memory/              # daily logs (YYYY-MM-DD.md)
├── skills/
│   ├── san5-x11vnc/
│   │   ├── SKILL.md
│   │   └── scripts/x11vnc_start.sh
│   ├── san5-starter/
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       ├── san5_start.sh
│   │       └── san5-dosbox.conf
│   ├── san5-ui/
│   │   └── SKILL.md     # game UI coords (no scripts)
│   ├── mouse/
│   │   ├── SKILL.md
│   │   └── scripts/san5_mouse.py
│   ├── screenshot/
│   │   ├── SKILL.md
│   │   └── scripts/san5_capture.py
│   └── easyocr/
│       ├── SKILL.md
│       └── scripts/
│           ├── bootstrap.sh
│           └── san5_ocr.py
```

Vision play: `san5_capture.py` / `san5_ocr.py` → `san5_mouse` move → debug → click. Verified coords: `skills/san5-ui/SKILL.md`.

## Local OCR

Use `easyocr` when the target is visible text on screen:

```bash
uv run --group easyocr python skills/easyocr/scripts/san5_ocr.py --json
uv run --group easyocr python skills/easyocr/scripts/san5_ocr.py --json --match 確認
```

`--json` output includes OCR `targets[]` plus `recommended_click` when `--match` succeeds. Verify with `debug -v` before clicking; promote good coords to `san5-ui`.

## `san5_mouse.py`

Full CLI and env vars are documented in `skills/mouse/SKILL.md`.

```bash
python3 skills/mouse/scripts/san5_mouse.py -h
python3 skills/mouse/scripts/san5_mouse.py -a debug -v
```

## Cursor visibility (VNC)

- `x11vnc_start.sh` hides the X11 pointer; only the in-game cursor shows
- If the VNC client shows two cursors, disable local cursor in the viewer

## Troubleshooting

| Problem | What to try |
|---------|-------------|
| Clicks do nothing | `-a click` after `-a move`; avoid `-a release` unless stuck |
| Wrong position | `-a debug`; restart stack so DOSBox is at 0,0 1024×768 |
| DOSBox not found | `export SAN5_DISPLAY=:99`; start VNC + game |
| Stuck capture | `-a release`, then move+click again or restart DOSBox |
| OCR wrong coords | Re-run `san5_ocr.py --json`; verify with `debug -v`; update `san5-ui` when correct |

## Stopping

```bash
pkill -f 'dosbox.*san5-dosbox'
pkill -9 x11vnc Xvfb    # tears down VNC stack
```
