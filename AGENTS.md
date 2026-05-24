# AGENTS.md — san5 workspace

OpenClaw workspace for **Romance of the Three Kingdoms V** on VNC + DOSBox.

## Skills (read SKILL.md before using)

| Skill | Purpose |
|-------|---------|
| `skills/san5-runtime/` | VNC + DOSBox launch (`san5_start.sh` includes first 確認 mouse sync) |
| `skills/dosbox-mouse/` | Pointer move/click via `dosbox_mouse.py` |
| `skills/screenshot/` | Capture framebuffer with `scrot` for vision |
| `skills/minicpm-vision/` | MiniCPM-V API when agent has no native vision |

Environment-specific values (game path, VNC host, ports) live in **`TOOLS.md`**, not here.

### Mouse: sync ≠ capture

Read `skills/dosbox-mouse/SKILL.md` (**Concepts**) for detail. Short version:

| Term | Command |
|------|---------|
| Sync (game cursor follows X11) | `move -p X Y --sync` |
| Capture (DOSBox accepts mouse) | `click` — no separate action; not the same as `--sync` |
| Release (uncapture) | `release` |

Workflow: `move --sync` → `debug -v` → `click`. First 確認 dialog needs an extra `click` on the dialog body to capture before aiming the button.

## Game window

- Resolution: **1024×768** (VNC display = DOSBox window, origin top-left)
- Origin: `(0, 0)` → `(1024, 768)`; DOSBox pinned at `(0, 0)` on `:99`
- Typical UI coords scale with window size; re-learn after layout change

## Play workflow

1. Check VNC: `ps aux | grep x11vnc` — start runtime skill if needed
2. Launch game if DOSBox is not running
3. User views via VNC (`TOOLS.md` for host:port)
4. Use **dosbox-mouse** for interaction; describe what you see to the user
5. For vision-driven play: look → click → verify (see below)

### No native vision (MiniCPM-V)

The agent **cannot read PNGs**. Use `minicpm-vision` — it returns descriptions **and** parsed pixel coords (with auto-retry if the model sends fractions instead of pixels).

**Always use `--json`** and read `recommended_click.use_click` (calibrated when cursor anchor worked):

```bash
./skills/minicpm-vision/scripts/san5_look.sh
# debug cursor → capture → analyze → calibrated coords
```

`san5_look.sh` auto-calibrates: runs `dosbox_mouse -a debug` for the true cursor position, asks MiniCPM-V to find the game cursor in the PNG, computes offset, shifts all button coords.

Then click: `dosbox_mouse.py -a move -p CX CY --sync` → **debug -v** → click (first 確認: see `dosbox-mouse`).

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
