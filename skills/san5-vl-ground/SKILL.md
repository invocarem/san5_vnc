---
name: san5-vl-ground
description: >-
  Ground UI elements in san5 screenshots via Qwen3-VL Grounding API (/v1/ground)
  and return pixel click coordinates. Use when EasyOCR fails or for non-text UI.
  Does not use LiteLLM or OpenAI chat completions.
---

# san5 VL Ground (Qwen3-VL Grounding API)

Direct HTTP client for the **Qwen3-VL Grounding API** (FastAPI on spark1, etc.):

| Endpoint | Use |
|----------|-----|
| `POST /v1/ground` | Multipart upload (default) — image from this machine |
| `POST /v1/ground/path` | JSON body with `image_path` readable **on the server host** |
| `GET /health` | Liveness |

**Not** OpenAI-compatible: no `/v1/models` or `/v1/chat/completions`. Do not route through LiteLLM.

Script: **`scripts/san5_vl_ground.py`** — same JSON contract as easyocr (`targets[]`, `recommended_click`, `summary_line`).

## Setup

```bash
./skills/san5-vl-ground/scripts/bootstrap.sh
export SAN5_GROUND_BASE_URL=http://100.109.56.33:5080   # or spark1:5080
```

Check server:

```bash
curl -sS "$SAN5_GROUND_BASE_URL/health"
```

OpenAPI docs on the server: `{SAN5_GROUND_BASE_URL}/docs`

## Quick start

Upload from game host (capture + ground + JSON):

```bash
uv run --group san5-vl-ground python skills/san5-vl-ground/scripts/san5_vl_ground.py --json
```

Match a label:

```bash
uv run --group san5-vl-ground python skills/san5-vl-ground/scripts/san5_vl_ground.py --json --match 確認
```

Ground only (PNG exists):

```bash
uv run --group san5-vl-ground python skills/san5-vl-ground/scripts/san5_vl_ground.py --no-capture --json
```

Image already on the **server** filesystem:

```bash
uv run --group san5-vl-ground python skills/san5-vl-ground/scripts/san5_vl_ground.py --json --ground-path \
  --no-capture /path/on/server/screenshots/latest.png
```

Custom prompt:

```bash
uv run --group san5-vl-ground python skills/san5-vl-ground/scripts/san5_vl_ground.py --json \
  --prompt "Find the 開始新遊戲 button"
```

## Output

Server returns `detections[]` with `label`, `bbox_pixels`, `center_pixels`. The script maps these to `targets[]` in 1024×768 san5 space (scales if the server resized the image).

`--json` also includes `model_output` when useful; use `--raw` to always echo it in text mode.

## Workflow with mouse

Same as easyocr:

1. `san5_vl_ground.py --json`
2. `recommended_click.click` → `move --sync` → `debug -v` → `click`
3. Re-run after dialog clicks
4. Promote verified coords to `skills/san5-ui/SKILL.md`

## Environment

| Variable | Default | Meaning |
|----------|---------|---------|
| `SAN5_GROUND_BASE_URL` | `http://127.0.0.1:5080` | Server root (no `/v1` suffix) |
| `SAN5_GROUND_PROMPT` | built-in UI prompt | Default grounding prompt |
| `SAN5_GROUND_MAX_PIXELS` | (unset) | Optional resize limit on server |
| `SAN5_GROUND_TIMEOUT` | `180` | HTTP timeout (seconds) |
| `SAN5_GROUND_RAW` | `0` | Set `1` to pass `raw=true` to server |
| `SAN5_SCREENSHOT` | `screenshots/latest.png` | PNG after capture |

## When to use

| Task | Tool |
|------|------|
| Clear Chinese/English labels | `easyocr` |
| Icons, map bar, grounding server | **san5-vl-ground** |
| Known coords | `san5-ui` |

## Limitations

- Grounding can take several seconds per frame.
- `--ground-path` only works if the PNG path exists on the **same machine as the API server**.
- Always verify with `san5_mouse.py -a debug -v` before clicking.
