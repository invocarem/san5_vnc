---
name: minicpm-vision
description: >-
  Analyze san5 screenshots via ModelBest MiniCPM-V-4.6 when the agent has no
  native vision. Captures or loads a PNG, calls api.modelbest.cn, parses pixel
  coordinates (with auto-retry), returns JSON for dosbox-mouse. Use when the
  agent has no in-chat image support.
---

# san5 MiniCPM-V vision (no native vision)

When the **agent cannot read PNGs**, use **openbmb/MiniCPM-V-4.6** on ModelBest instead of in-process vision.

The model often returns **descriptions without pixel coords** (or normalized 0–1 fractions). This skill **parses and converts** them, and **auto-retries** with a JSON-only prompt when needed.

## Quick start (preferred)

```bash
export MODELBEST_API_KEY="sk-pQ8L2zF3XmR5kY9wV4jB7hN1tC6vM0xG3aD5sH2bJ9lK4cZ8"   # free public trial key (docs)

# capture + analyze + cursor-calibrated coords (default with --capture)
./skills/minicpm-vision/scripts/san5_look.sh

# same, explicit path (--capture auto-enables calibration)
python3 skills/minicpm-vision/scripts/analyze_screenshot.py --capture --json
```

Read **`recommended_click.use_click`** from JSON (prefer over raw `click`):

```json
{
  "cursor": {
    "debug": [152, 214],
    "vision": [148, 210],
    "offset": [4, 4],
    "active": true,
    "reason": "applied offset (+4,+4) from cursor anchor"
  },
  "recommended_click": {
    "label": "開始新遊戲",
    "click": [152, 214],
    "calibrated_click": [156, 218],
    "use_click": [156, 218]
  }
}
```

Progress lines print on stderr: `[san5-vision  12.3s] API request → …`

## End-to-end with dosbox-mouse

1. **Tell the user** you are looking at the screen (~30s)
2. **Analyze** — `san5_look.sh` or `--capture --json`
3. **Report** `summary_line` in chat
4. **Click** — from `recommended_click.use_click`:

   ```bash
   CX=156 CY=218
   python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a move -p $CX $CY --sync
   sleep 0.2
   python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a debug   # must show inside window near target
   python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a click
   ```

   First 確認 dialog (mouse not captured): see `san5-ui` → **first_cd_confirm** (or `dosbox-mouse` SKILL.md).

5. **Verify** — run `san5_look.sh` again if the dialog is still open or debug was off-target

## Cursor calibration (debug anchor)

With `--capture` (default in `san5_look.sh`):

1. **`dosbox_mouse -a debug`** — ground-truth pointer from xdotool
2. **`move -p X Y --sync`** — redraw the game cursor at that pixel before `scrot`
3. **Capture + analyze** — separate cursor JSON pass if needed
4. **Offset** — `debug − vision` applied to button coords **only** when offset &lt; 80px and vision’s cursor tip is in the expected screen region

If calibration is skipped (large offset, vision cursor on wrong side of screen), use layout-filtered `click` coords as-is. Check `cursor.active`, `cursor.reason`, and `warnings[]`.

**Do not** assume debug `(940, 210)` is wrong on the **map** screen — the command UI lives on the **right** (x ≥ 540). A centered main-menu screenshot is a different `screen_type`.

Disable: `--no-calibrate`

## Agent visibility rules

| When | Say in chat |
|------|-------------|
| Before capture/API | `Looking at the screen (MiniCPM-V, ~30s)…` |
| After JSON returns | Paste `summary_line` |
| Before click | `Clicking <label> at (X,Y)…` |
| After click (if unsure) | `Verifying screen…` |

Never stay silent for 15+ seconds during vision work.

## API (ModelBest)

| Item | Value |
|------|-------|
| Base URL | `https://api.modelbest.cn/v1` |
| Endpoint | `POST /chat/completions` |
| Model | `MiniCPM-V-4.6-Instruct` (default) or `MiniCPM-V-4.6-Thinking` |
| Auth | `Authorization: Bearer $MODELBEST_API_KEY` |
| Image | base64 data URL in `messages[].content[]` as `image_url` |

Official reference: [MiniCPM-V docs/api.md](https://github.com/OpenBMB/MiniCPM-V/blob/main/docs/api.md)

## Environment

| Variable | Default | Meaning |
|----------|---------|---------|
| `MODELBEST_API_KEY` | (required) | Bearer token; use public trial key above or your own |
| `MODELBEST_API_BASE` | `https://api.modelbest.cn/v1` | API base URL |
| `MODELBEST_MODEL` | `MiniCPM-V-4.6-Instruct` | Model id |
| `MODELBEST_TIMEOUT` | `120` | HTTP timeout (seconds) |
| `SAN5_DISPLAY` / `SAN5_SCREEN_*` | see `screenshot` skill | Used with `--capture` |

## Script options

```bash
python3 skills/minicpm-vision/scripts/analyze_screenshot.py -h
```

| Flag | Purpose |
|------|---------|
| `--capture` | `scrot` then analyze (auto-calibrates via debug cursor) |
| `--json` | structured output with `targets`, `recommended_click.use_click`, `cursor` |
| `--no-calibrate` | skip debug-cursor anchor (even with `--capture`) |
| `-o FILE` | write raw markdown to file |
| `--prompt TEXT` | override san5 bbox prompt (single call, no auto-retry) |
| `--no-retry` | skip JSON retry when markdown lacks pixel coords |
| `--quiet` | hide `[san5-vision]` progress on stderr |
| `--model NAME` | e.g. `MiniCPM-V-4.6-Thinking` |
| `--raw` | dump full parsed result JSON (includes raw_markdown) |

## Coordinate handling

1. **Debug anchor** — `dosbox_mouse -a debug` before capture (when calibrating)
2. **Primary pass** — markdown template with integer pixel bboxes + game cursor tip
3. **Parser** — extracts table rows; converts normalized 0–1 fractions to pixels
4. **Calibration** — offset from debug vs vision cursor applied to all targets
5. **Retry pass** — if no valid targets, second API call asks for JSON array only
6. **Output** — `use_click` ready for `move -p CX CY --sync`; verify with `debug -v`, then `click`

## Prerequisites

| Step | Skill |
|------|-------|
| Game on `:99` | `san5-starter` |
| Capture | `screenshot` (`scrot`) |
| Click | `dosbox-mouse` |

Network access to `api.modelbest.cn` is required.

## Troubleshooting

| Problem | What to try |
|---------|-------------|
| `MODELBEST_API_KEY` unset | `export` the key from this doc or `TOOLS.md` |
| DNS / connection errors | Check outbound HTTPS; retry with longer `--timeout` |
| Empty `targets` after retry | Read `raw_markdown` / describe screen to user; re-capture |
| `coord_confidence: low` | Model put buttons on the map (left); regional retry should run — if still empty, use `skills/san5-ui` anchors |
| Inconsistent coords across runs | Different `screen_type` (menu vs map) or stale PNG; always `--capture` fresh |
| Debug cursor far right | Normal on **map** screen (right panel); not normal on **main_menu** (center ~x 512) |
| Wrong button coords | Check `coords_source` (`retry_regional` is best for map); verify with `debug -v` before click |
| Slow | Normal — 20–60s (up to 2 API calls on map); keep user updated via chat + stderr progress |
