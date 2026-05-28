---
name: easyocr
description: >-
  Locate visible Chinese and English UI text in san5 DOSBox screenshots with
  EasyOCR and return pixel coordinates for clicks. Use when a button/menu item
  is text-driven (for example 確認 or 開始新遊戲), or when you want to match a
  specific label in the current screenshot.
---

# san5 EasyOCR

Local OCR for san5 screenshots. Primary tool for **text-heavy menus and dialogs** where the clickable target is the label itself.

Script: **`scripts/san5_ocr.py`** — captures (via `san5_capture.py`) then runs EasyOCR.

Use it when:

- the screen has readable Chinese or English button text
- you need bbox/click coordinates for `san5_mouse.py`
- you want to find a specific label such as `確認`, `取消`, or `開始新遊戲`

Do **not** rely on OCR alone for non-text UI, stylized icons, or map elements with no readable label — use `skills/san5-ui` anchors or native vision on the PNG.

## Setup

Workspace Python dependencies are managed with `uv` at the repo root.

```bash
uv python install 3.12   # optional
./skills/easyocr/scripts/bootstrap.sh
```

First OCR run may download EasyOCR model files to the user cache. That needs network access.

## Quick start

Capture + OCR + JSON (preferred):

```bash
uv run --group easyocr python skills/easyocr/scripts/san5_ocr.py --json
```

Match a specific label:

```bash
uv run --group easyocr python skills/easyocr/scripts/san5_ocr.py --json --match 確認
uv run --group easyocr python skills/easyocr/scripts/san5_ocr.py --json --match 開始新遊戲
```

OCR only (PNG must already exist):

```bash
uv run --group easyocr python skills/easyocr/scripts/san5_ocr.py --no-capture --json
```

Capture only (no OCR):

```bash
python3 skills/screenshot/scripts/san5_capture.py
```

## Output

`--json` prints:

- `targets[]` with `label`, `bbox`, `click`, and `confidence`
- `recommended_click` when `--match TEXT` finds a label
- `summary_line` for quick chat/status updates

## Workflow with mouse

1. Run `san5_ocr.py --json` (capture + OCR by default)
2. Read `recommended_click.click` (or pick from `targets[]`)
3. Move and verify before clicking:

```bash
CX=510 CY=436
python3 skills/mouse/scripts/san5_mouse.py -a move -p $CX $CY --sync
sleep 0.2
python3 skills/mouse/scripts/san5_mouse.py -a debug -v
python3 skills/mouse/scripts/san5_mouse.py -a click
```

4. Run `san5_ocr.py --json` again to verify the screen changed
5. Promote good coords to `skills/san5-ui/SKILL.md`

For the first CD/確認 dialog, follow `skills/san5-ui/SKILL.md` (mouse capture rules).

## Environment

| Variable | Default | Meaning |
|----------|---------|---------|
| `SAN5_SCREENSHOT` | `screenshots/latest.png` | PNG path after default capture |
| `SAN5_EASYOCR_LANGS` | `ch_tra,en` | OCR languages |
| `SAN5_EASYOCR_MIN_CONFIDENCE` | `0.5` | Minimum accepted OCR confidence |
| `SAN5_EASYOCR_GPU` | `0` | Set to `1` to enable GPU mode |

Capture display vars (`SAN5_DISPLAY`, `SAN5_SCREEN_*`, `SAN5_RUN`) are documented in `skills/screenshot/SKILL.md`.

## Limitations

- OCR sees **text**, not intent — the agent chooses the next label to `--match`.
- Low-contrast or decorative fonts may OCR poorly.
- Non-text UI needs `san5-ui` anchors or native vision.
- Always verify with `san5_mouse.py -a debug -v` before clicking.
