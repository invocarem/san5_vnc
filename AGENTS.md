# AGENTS.md — san5 workspace

OpenClaw workspace for **Romance of the Three Kingdoms V** on VNC + DOSBox.

## Skills (read SKILL.md before using)

| Skill | Purpose |
|-------|---------|
| `skills/san5-x11vnc/` | Virtual display + VNC (`x11vnc_start.sh`) |
| `skills/san5-starter/` | Launch DOSBox + game (`san5_start.sh`) |
| `skills/san5-ui/` | Known UI coords and click procedures (markdown only) |
| `skills/mouse/` | Pointer move/click via `san5_mouse.py` |
| `skills/screenshot/` | Capture framebuffer with `scrot` for vision |
| `skills/easyocr/` | Local OCR for visible text labels in screenshots |

Environment-specific values (game path, VNC host, ports) live in **`TOOLS.md`**, not here.

### Mouse: sync ≠ capture

Read `skills/mouse/SKILL.md` (**Concepts**) for detail. Short version:

| Term | Command |
|------|---------|
| Sync (game cursor follows X11) | `move -p X Y --sync` |
| Capture (DOSBox accepts mouse) | `click` — no separate action; not the same as `--sync` |
| Release (uncapture) | `release` |

Workflow: `move --sync` → `debug -v` → `click`. First 確認 dialog: see `san5-ui` → **first_cd_confirm** (capture click on dialog body, then 確認).

## Game window

- Resolution: **1024×768** (VNC display = DOSBox window, origin top-left)
- Origin: `(0, 0)` → `(1024, 768)`; DOSBox pinned at `(0, 0)` on `:99`
- Typical UI coords scale with window size; re-learn after layout change

## Play workflow

1. Check VNC: `ps aux | grep x11vnc` — start `san5-x11vnc` if needed
2. Launch game if DOSBox is not running (`san5-starter`)
3. User views via VNC (`TOOLS.md` for host:port)
4. Use **mouse** for interaction; describe what you see to the user
5. For vision-driven play: capture → OCR → click → verify (see below)

### Local OCR (EasyOCR) — primary screen analysis

Use `easyocr` for text labels (`確認`, `取消`, `開始新遊戲`, etc.). It captures a fresh frame, runs local OCR, and returns bbox/click coordinates.

```bash
uv run --group easyocr python skills/easyocr/scripts/san5_ocr.py --json
uv run --group easyocr python skills/easyocr/scripts/san5_ocr.py --json --match 確認
```

Use `recommended_click.click` from JSON when `--match` succeeds, then **always** verify with `san5_mouse -a debug -v` before clicking. Promote verified coords to `skills/san5-ui/SKILL.md`.

For screens without readable text, use **san5-ui** anchors or agent native vision on the PNG if available.

### Visibility — never go silent

OCR can take several seconds on first run (model download). The user should know you are working.

1. **Before** capture/OCR: e.g. `Capturing screen and running OCR…`
2. **Run** `san5_ocr.py` — progress on stderr
3. **After** analysis, report `summary_line` from JSON in chat
4. **Before** each click: `Clicking <label> at (X,Y)…` then move `--sync` → **debug -v** (within ~12 px) → click
5. **After** click: capture/OCR again if the dialog may still be open

If `--match` fails or coords look wrong, say so — do not click blindly. Re-run `san5_ocr.py` (capture + OCR) for a fresh frame.

## Safety

- Never `pkill -9 x11vnc` / `Xvfb` without asking
- Confirm DOSBox is running before click sequences
- Run `san5_mouse.py -a debug` before long coordinate chains

## Memory

- **Daily:** `memory/YYYY-MM-DD.md` — session logs, raw notes
- **Long-term:** `MEMORY.md` — curated coords, scenarios, lessons (main session only)
