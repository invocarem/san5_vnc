# AGENTS.md — san5 workspace

OpenClaw workspace for **Romance of the Three Kingdoms V** on VNC + DOSBox.

## Skills (read SKILL.md before using)

| Skill | Purpose |
|-------|---------|
| `skills/san5-x11vnc/` | Virtual display + VNC (`x11vnc_start.sh`) |
| `skills/san5-starter/` | Launch DOSBox + game (`san5_start.sh`) |
| `skills/san5-ui/` | Known UI coords and click procedures (markdown only) |
| `skills/dosbox-mouse/` | Pointer move/click via `dosbox_mouse.py` |
| `skills/screenshot/` | Capture framebuffer with `scrot` for vision |
| `skills/dosbox-easyocr/` | Local OCR for visible text labels in screenshots |
| `skills/minicpm-vision/` | MiniCPM-V API when agent has no native vision |

Environment-specific values (game path, VNC host, ports) live in **`TOOLS.md`**, not here.

### Mouse: sync ≠ capture

Read `skills/dosbox-mouse/SKILL.md` (**Concepts**) for detail. Short version:

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
4. Use **dosbox-mouse** for interaction; describe what you see to the user
5. For vision-driven play: look → click → verify (see below)

### Local OCR (EasyOCR)

When the target is a visible text label, prefer `dosbox-easyocr` first. It is local, fast, and returns bbox/click coordinates for labels such as `確認`, `取消`, and `開始新遊戲`.

```bash
./skills/dosbox-easyocr/scripts/san5_ocr.sh
./skills/dosbox-easyocr/scripts/san5_ocr.sh san5_screenshot.png --match 確認
```

Use `recommended_click.click` from JSON when `--match` succeeds, then verify with `dosbox_mouse -a debug -v` before clicking.

### No native vision (MiniCPM-V)

The agent **cannot read PNGs**. Use `minicpm-vision` when OCR is not enough — it returns descriptions, picks likely next actions, and parses pixel coords (with auto-retry if the model sends fractions instead of pixels).

**Always use `--json`** and read `recommended_click.use_click` (calibrated when cursor anchor worked):

```bash
./skills/minicpm-vision/scripts/san5_look.sh
# debug cursor → capture → analyze → calibrated coords
```

`san5_look.sh` auto-calibrates: runs `dosbox_mouse -a debug` for the true cursor position, asks MiniCPM-V to find the game cursor in the PNG, computes offset, shifts all button coords.

Then click: `dosbox_mouse.py -a move -p CX CY --sync` → **debug -v** → click (first 確認: see `san5-ui`).

### Visibility — never go silent

Vision API calls take **20–60 seconds**. The user must always know you are working — do not wait for them to ask.

1. **Before** a long step, send one short line in chat: e.g. `Looking at the screen (MiniCPM-V, ~30s)…`
2. **Run** the script — `[san5-vision]` progress prints on stderr in the terminal
3. **After** analysis, report `summary_line` from JSON in chat: e.g. `Main menu → click 開始新遊戲 at (512,308) [calibrated (+4,+2)]`
4. **Before** each click: `Clicking 開始新遊戲 at (512,308)…` then move `--sync` → **debug -v** (must match target within ~12px) → click
5. **After** click: `Capturing again to verify…` if the dialog may still be open

If coords are missing after retry, say so and describe the screen — do not silently stall.

## Safety

- Never `pkill -9 x11vnc` / `Xvfb` without asking
- Confirm DOSBox is running before click sequences
- Run `dosbox_mouse.py -a debug` before long coordinate chains

## Memory

- **Daily:** `memory/YYYY-MM-DD.md` — session logs, raw notes
- **Long-term:** `MEMORY.md` — curated coords, scenarios, lessons (main session only)
