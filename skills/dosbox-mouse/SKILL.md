---
name: dosbox-mouse
description: >-
  Move and click inside the DOSBox san5 window on the VNC display using
  window-relative coordinates (typically 1024×768). Use for mouse control,
  click/release capture, splash dismiss, pointer debug, and vision-driven clicks
  after screenshot analysis.
---

# DOSBox mouse control

Script: `skills/dosbox-mouse/scripts/dosbox_mouse.py`

Coordinates are **window-relative** (origin top-left of the DOSBox window), same as PNG pixels from `scrot`.

```bash
python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -h

python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a move   -p X Y [--sync]
python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a debug  [-v]
python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a click
python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a rclick
python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a release
python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a dismiss
```

## Concepts: sync, capture, release

DOSBox (`autolock=false`) separates **where the pointer is** from **whether the game owns the mouse**.

| Term | Meaning | CLI |
|------|---------|-----|
| **Sync** | Warp X11 to `(X,Y)` and jiggle so the **game cursor** redraws at that position | `move -p X Y --sync` |
| **Capture** | DOSBox **accepts** mouse input (first click inside the window, or again after release) | `click` at current position — **no separate capture action** |
| **Release** | DOSBox **stops** holding the pointer (Ctrl+F10) | `release` |

**`move --sync` does not capture.** You can be synced (game cursor visible at the right place) but not captured (clicks still ignored). **Capture is always a left click** via `click`, usually after `move --sync` and `debug -v`.

**`release` is not the opposite of sync** — it uncaptures input; it does not “unsync” the cursor. After `release`, run `move --sync` → `click` again before more game clicks.

Plain `move -p X Y` (no `--sync`) only warps X11 — faster when the game cursor already matches and capture is already active.

## Workflow

**Normal** (mouse already captured in DOSBox):

1. `-a move -p X Y --sync` — warp X11 pointer and jiggle so the game cursor follows
2. `-a debug -v` — confirm `inside window (X, Y)` is on target (within ~12 px of vision coords)
3. `-a click` — left-click at current position

**First dialog** (確認 / CD prompt — game ignores xdotool until you click inside DOSBox once). Coords: `san5-ui` → **first_cd_confirm**.

1. `-a move -p CX CY --sync` on dialog body (not the button)
2. `-a click` — **captures** mouse in DOSBox
3. `-a move -p X Y --sync` — move game cursor to 確認
4. sleep ~0.2s if the cursor needs time to settle
5. `-a debug -v` — verify position before clicking
6. `-a click` — confirm the button

After `san5_start.sh`, run the **first_cd_confirm** procedure in `skills/san5-ui/SKILL.md` (coords + capture sequence).

After `-a release`, run `move --sync` → `click` again to re-capture before more game clicks.

## Vision-driven play

No separate click skill — the agent orchestrates:

1. **Screenshot** — `scrot -D :99 -a 0,0,1024,768 san5_screenshot.png` (`skills/screenshot`)
2. **Analyze** — native vision on the PNG, or `skills/minicpm-vision` (`san5_look.sh` / `--capture --json`) if the agent cannot see images. Use `recommended_click.use_click` from JSON.
3. **Click** — use bbox from analysis: `cx = (x1+x2)//2`, `cy = (y1+y2)//2`, then move → debug → click

```bash
python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a move -p CX CY --sync
sleep 0.2
python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a debug -v
python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a click
```

4. **Screen verify** — capture again; retry if dialog still open or debug showed wrong position

### Vision output template

After analyzing a screenshot, record:

```markdown
## Screen
- type: dialog | main_menu | map | battle | other
- summary: one line

## Message
- text: (if any)

## Targets
| label | bbox (x1,y1,x2,y2) | click (cx,cy) |
|-------|---------------------|---------------|
| (from screenshot) | integers only | center of bbox |

For verified san5 anchors (e.g. CD 確認), see `skills/san5-ui/SKILL.md`.

## Next action
- click: 確認
```

Rules: `(x1,y1)` top-left, `(x2,y2)` bottom-right; click center must lie inside bbox.

### Safety

- Do not click if `debug` shows cursor far from target — take a new screenshot and re-analyze bbox
- Always tie coordinates to a visible bbox from the **current** screenshot
- After `release`, `-a click` again before more clicks (DOSBox must re-capture the pointer)

## Environment

| Variable | Default | Meaning |
|----------|---------|---------|
| `SAN5_DISPLAY` | `:99` | X11 display |
| `SAN5_LOGICAL_WIDTH` / `SAN5_LOGICAL_HEIGHT` | `1024` / `768` | For `--scale` |
| `SAN5_WAKE_CURSOR` | `1` | Pointer jiggle when `move --sync` (disable if jiggle causes issues) |
| `SAN5_CLICK_SCREEN_SYNC` | `0` | `1` = old slow screen `mousemove --sync` before click (~15s on Xvfb) |
| `SAN5_CLICK_SCREEN_NUDGE` | `1` | Fast unsynced screen warp before mousedown (disable if clicks miss) |
| `SAN5_SETTLE_SEC` | `0.2` | Optional sleep after move before debug (see `san5-ui` procedures) |

Full list and troubleshooting: workspace `README.md`.

## Troubleshooting

| Problem | What to try |
|---------|-------------|
| Wrong button | Re-capture; tighten bbox; click center |
| debug off-target | Increase settle sleep; re-analyze bbox; do not click |
| Clicks do nothing | May need **capture**: `move --sync` → `click` on dialog body, then aim button |
| Clicks miss / first dialog | `move --sync` → `click` (capture) → `move --sync` → `debug -v` → `click` |
| Confused sync vs capture | See **Concepts** above — `--sync` ≠ capture |
| Stale screen | Capture again after each click |
| No DOSBox | Start game; confirm `SAN5_DISPLAY=:99` |
