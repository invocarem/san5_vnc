# AGENTS.md — san5 workspace

OpenClaw workspace for **Romance of the Three Kingdoms V** on VNC + DOSBox.

## Skills (read SKILL.md before using)

| Skill | Purpose |
|-------|---------|
| `skills/san5-runtime/` | VNC + DOSBox launch (`san5_start.sh` includes first 確認 mouse sync) |
| `skills/dosbox-mouse/` | Pointer move/click/grab via `dosbox_mouse.py` |
| `skills/screenshot/` | Capture framebuffer with `scrot` for vision |
| `skills/vision-click/` | Analyze screenshot, click targets (`click_target.py`) |

Environment-specific values (game path, VNC host, ports) live in **`TOOLS.md`**, not here.

## Game window

- Resolution: **1024×768** (VNC display = DOSBox window, origin top-left)
- Origin: `(0, 0)` → `(1024, 768)`; DOSBox pinned at `(0, 0)` on `:99`
- Typical UI coords scale with window size; re-learn after layout change

## Play workflow

1. Check VNC: `ps aux | grep x11vnc` — start runtime skill if needed
2. Launch game if DOSBox is not running
3. User views via VNC (`TOOLS.md` for host:port)
4. Use **dosbox-mouse** for interaction; describe what you see to the user
5. For vision-driven play: `scrot` → analyze PNG → click (first 確認 dialog: capture→move→grab, see vision-click)

## Safety

- Never `pkill -9 x11vnc` / `Xvfb` without asking
- Confirm DOSBox is running before click sequences
- Run `dosbox_mouse.py -a debug` before long coordinate chains

## Memory

- **Daily:** `memory/YYYY-MM-DD.md` — session logs, raw notes
- **Long-term:** `MEMORY.md` — curated coords, scenarios, lessons (main session only)
