# AGENTS.md — san5 workspace

OpenClaw workspace for **Romance of the Three Kingdoms V** on VNC + DOSBox.

## Skills (read SKILL.md before using)

| Skill | Purpose |
|-------|---------|
| `skills/san5-runtime/` | VNC stack + DOSBox launch (`x11vnc_start.sh`, `san5_start.sh`, `san5-dosbox.conf`) |
| `skills/dosbox-mouse/` | Pointer move/click/grab via `dosbox_mouse.py` |
| `skills/screenshot/` | *(planned)* capture framebuffer for vision |
| `skills/vision-click/` | *(planned)* find UI targets and click |

Environment-specific values (game path, VNC host, ports) live in **`TOOLS.md`**, not here.

## Game window

- Resolution: **800×600** (logical coordinates)
- Origin: top-left `(0, 0)` → bottom-right `(800, 600)`
- Typical UI (RTK V): menu ~(400, 550); map tiles in upper area

## Play workflow

1. Check VNC: `ps aux | grep x11vnc` — start runtime skill if needed
2. Launch game if DOSBox is not running
3. User views via VNC (`TOOLS.md` for host:port)
4. Use **dosbox-mouse** for interaction; describe what you see to the user
5. For vision-driven play, use screenshot + vision-click skills when added

## Safety

- Never `pkill -9 x11vnc` / `Xvfb` without asking
- Confirm DOSBox is running before click sequences
- Run `dosbox_mouse.py -a debug` before long coordinate chains

## Memory

- **Daily:** `memory/YYYY-MM-DD.md` — session logs, raw notes
- **Long-term:** `MEMORY.md` — curated coords, scenarios, lessons (main session only)
