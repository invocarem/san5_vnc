---
name: dosbox-easyocr
description: >-
  Locate visible Chinese and English UI text in san5 DOSBox screenshots with
  EasyOCR and return pixel coordinates for clicks. Use when a button/menu item
  is text-driven (for example 確認 or 開始新遊戲), when you want a local OCR
  alternative to minicpm-vision, or when you want to match a specific label in
  the current screenshot.
---

# DOSBox EasyOCR

Local OCR for san5 screenshots. This is best for **text-heavy menus and dialogs** where the clickable target is the label itself.

Use it when:

- the screen has readable Chinese or English button text
- you want a local fallback or complement to `minicpm-vision`
- you want to find a specific label such as `確認`, `取消`, or `開始新遊戲`

Do **not** rely on OCR alone for non-text UI, stylized icons, or map elements with no readable label.

## Setup

Workspace Python dependencies are managed with `uv` at the repo root.

```bash
# Optional: install a uv-managed Python first
uv python install 3.12

# Sync the EasyOCR dependency group
./skills/dosbox-easyocr/scripts/bootstrap.sh
```

First OCR run may download EasyOCR model files to the user cache. That needs network access.

## Quick start

Capture + OCR + JSON:

```bash
./skills/dosbox-easyocr/scripts/san5_ocr.sh
```

Match a specific label:

```bash
./skills/dosbox-easyocr/scripts/san5_ocr.sh san5_screenshot.png --match 確認
```

Direct script use:

```bash
uv run --group easyocr python skills/dosbox-easyocr/scripts/analyze_screenshot.py --capture --json
uv run --group easyocr python skills/dosbox-easyocr/scripts/analyze_screenshot.py san5_screenshot.png --match 開始新遊戲
```

## Output

`--json` prints:

- `targets[]` with `label`, `bbox`, `click`, and `confidence`
- `recommended_click` when `--match TEXT` finds a label
- `summary_line` for quick chat/status updates

Example shape:

```json
{
  "targets": [
    {
      "label": "確認",
      "bbox": [460, 420, 560, 452],
      "click": [510, 436],
      "confidence": 0.93
    }
  ],
  "recommended_click": {
    "label": "確認",
    "bbox": [460, 420, 560, 452],
    "click": [510, 436],
    "confidence": 0.93
  }
}
```

## Workflow with dosbox-mouse

1. Capture or run `san5_ocr.sh`
2. If possible, use `--match <label>` and read `recommended_click.click`
3. Move and verify before clicking:

```bash
CX=510 CY=436
python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a move -p $CX $CY --sync
sleep 0.2
python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a debug -v
python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a click
```

4. Capture again to verify the screen changed

For the first CD/確認 dialog, still follow `skills/san5-ui/SKILL.md` and `skills/dosbox-mouse/SKILL.md` because OCR does not replace DOSBox mouse-capture rules.

## Environment

| Variable | Default | Meaning |
|----------|---------|---------|
| `SAN5_DISPLAY` | `:99` | Display used by `scrot -D` |
| `SAN5_SCREEN_WIDTH` / `SAN5_SCREEN_HEIGHT` | `1024` / `768` | Capture size |
| `SAN5_EASYOCR_LANGS` | `ch_tra,en` | OCR languages |
| `SAN5_EASYOCR_MIN_CONFIDENCE` | `0.5` | Minimum accepted OCR confidence |
| `SAN5_EASYOCR_GPU` | `0` | Set to `1` to enable GPU mode |

## Limitations

- OCR sees **text**, not intent. It cannot decide the right next action the way `minicpm-vision` can.
- Low-contrast or decorative fonts may OCR poorly.
- Non-text buttons and map controls often still need `minicpm-vision` or known anchors from `san5-ui`.
- Always verify with `dosbox_mouse.py -a debug -v` before clicking.
