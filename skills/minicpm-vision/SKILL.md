---
name: minicpm-vision
description: >-
  Analyze san5 screenshots via ModelBest MiniCPM-V-4.6 when the agent has no
  native vision. Captures or loads a PNG, calls api.modelbest.cn, returns
  vision-click bboxes. Use for vision-click without in-chat image support.
---

# san5 MiniCPM-V vision (no native vision)

When the **agent cannot read PNGs**, use **openbmb/MiniCPM-V-4.6** on ModelBest instead of in-process vision.

## Quick start

```bash
export MODELBEST_API_KEY="sk-pQ8L2zF3XmR5kY9wV4jB7hN1tC6vM0xG3aD5sH2bJ9lK4cZ8"   # free public trial key (docs)

# capture + analyze in one step
python3 skills/minicpm-vision/scripts/analyze_screenshot.py --capture

# existing scrot output
scrot -D :99 -a 0,0,1024,768 san5_screenshot.png
python3 skills/minicpm-vision/scripts/analyze_screenshot.py san5_screenshot.png
```

Save output for the agent to parse:

```bash
python3 skills/minicpm-vision/scripts/analyze_screenshot.py --capture -o /tmp/san5_vision.md
```

## End-to-end with vision-click

1. **Analyze** (this skill) → markdown with `## Targets` bboxes
2. **Click** (`skills/vision-click`) — parse `bbox` / `click` from the table, then:

   ```bash
   python3 skills/vision-click/scripts/click_target.py --bbox X1 Y1 X2 Y2
   # first 確認 dialog only:
   python3 skills/vision-click/scripts/click_target.py --bbox X1 Y1 X2 Y2 --first-dialog
   ```

3. **Verify** — `--capture` again and re-run if the dialog is still open

## API (ModelBest)

| Item | Value |
|------|-------|
| Base URL | `https://api.modelbest.cn/v1` |
| Endpoint | `POST /chat/completions` |
| Model | `MiniCPM-V-4.6-Instruct` (default) or `MiniCPM-V-4.6-Thinking` |
| Auth | `Authorization: Bearer $MODELBEST_API_KEY` |
| Image | base64 data URL in `messages[].content[]` as `image_url` |

Official reference: [MiniCPM-V docs/api.md](https://github.com/OpenBMB/MiniCPM-V/blob/main/docs/api.md)

Text-only smoke test:

```bash
export MODELBEST_API_KEY="sk-pQ8L2zF3XmR5kY9wV4jB7hN1tC6vM0xG3aD5sH2bJ9lK4cZ8"
curl https://api.modelbest.cn/v1/chat/completions \
  -H "Authorization: Bearer $MODELBEST_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "MiniCPM-V-4.6-Instruct",
    "messages": [{"role": "user", "content": "Introduce yourself in one sentence."}]
  }'
```

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
| `--capture` | `scrot` then analyze |
| `-o FILE` | write markdown to file |
| `--prompt TEXT` | override san5 bbox prompt |
| `--model NAME` | e.g. `MiniCPM-V-4.6-Thinking` |
| `--raw` | dump full JSON response |

Default prompt asks for the same **vision-click output template** (screen type, message, targets table, next action). Coordinates are **1024×768** PNG space.

## Prerequisites

| Step | Skill |
|------|-------|
| Game on `:99` | `san5-runtime` |
| Capture | `screenshot` (`scrot`) |
| Click | `vision-click` + `dosbox-mouse` |

Network access to `api.modelbest.cn` is required.

## Troubleshooting

| Problem | What to try |
|---------|-------------|
| `MODELBEST_API_KEY` unset | `export` the key from this doc or `TOOLS.md` |
| DNS / connection errors | Check outbound HTTPS; retry with longer `--timeout` |
| Wrong button coords | Re-capture; use `--prompt` to stress tight bboxes |
| Empty targets | Game may be on map with no buttons; read `## Screen` / `## Message` |
