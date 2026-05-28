---
name: san5-ui
description: >-
  Known UI layouts and button coordinates for Romance of the Three Kingdoms V
  at 1024×768. Use before coordinate click chains, after launch for the CD
  confirm dialog, or to store verified anchors. Discover tentative coords with
  easyocr, then verify and promote rows here.
---

# san5 UI knowledge

Markdown-only catalog of **verified** screen layouts and click targets. No scripts in this skill — read coords here, then run `skills/mouse/scripts/san5_mouse.py`.

**Discovering new UI:** run `skills/easyocr/scripts/san5_ocr.py` (with `--match <label>` when you know the text). Use `recommended_click.click` from JSON for the first attempt. After `debug -v` confirms within ~12 px, copy bbox/click into the tables below.

## Coordinate system

- Image / window size: **1024×768**, origin **(0, 0)** top-left
- DOSBox pinned at **(0, 0)** on display `:99` (see `san5-starter`, `TOOLS.md`)
- `(x1,y1)` = bbox top-left; `(x2,y2)` = bottom-right; click = center unless noted
- Re-verify after resolution or layout changes; promote tentative OCR finds from `MEMORY.md` into this file

## first_cd_confirm

First dialog after splash: CD-ROM / 確認 prompt. DOSBox does not accept clicks until the pointer is **captured** once inside the window.

| Role | Value | Notes |
|------|-------|-------|
| Wait before acting | ~3 s | After splash Enter keys; OCR or screenshot if unsure |
| Capture point (dialog body) | **512, 384** | First `move --sync` + `click` to grab mouse |
| 確認 bbox | **432, 398** → **592, 422** | top-left → bottom-right |
| 確認 click center | **512, 410** | `(432+592)/2`, `(398+422)/2` |

### Procedure

From workspace root (`MOUSE=skills/mouse/scripts/san5_mouse.py`):

```bash
# 1) optional: wait for dialog (~3s after san5_start.sh splash)
sleep 3

# 2) capture pointer in DOSBox
python3 "$MOUSE" -a move -p 512 384 --sync
python3 "$MOUSE" -a click

# 3) click 確認
python3 "$MOUSE" -a move -p 512 410 --sync
sleep 0.2
python3 "$MOUSE" -a debug -v
python3 "$MOUSE" -a click
```

See `skills/mouse/SKILL.md` for sync vs capture vs release.

### Overrides

Pass different pixels by editing commands above, or export before each run:

- `SAN5_CAPTURE_X` / `SAN5_CAPTURE_Y` — capture point (default 512, 384)
- `SAN5_CONFIRM_X1` … `SAN5_CONFIRM_Y2` — bbox corners (defaults 432,398,592,422)

## Main menu

*(No verified rows yet — fill after EasyOCR + `debug -v` on your machine.)*

| Label | bbox (x1,y1,x2,y2) | click (cx,cy) | Status |
|-------|---------------------|---------------|--------|
| 開始新遊戲 | — | — | pending: `uv run --group easyocr python skills/easyocr/scripts/san5_ocr.py --match 開始新遊戲` |
| 讀取進度 | — | — | pending |
| 結束遊戲 | — | — | pending |

### OCR discovery workflow

```bash
# capture + list all text targets
uv run --group easyocr python skills/easyocr/scripts/san5_ocr.py --json

# or match one label
uv run --group easyocr python skills/easyocr/scripts/san5_ocr.py --match 開始新遊戲
```

1. Read `recommended_click` (or pick from `targets[]`) in JSON.
2. Click with `san5_mouse` move → `debug -v` → click.
3. If the hit is correct, paste bbox and click into the table above and set **Status** to `verified`.
4. If OCR bbox is wrong, adjust from VNC/screenshot and still verify with `debug -v` before marking verified.

Non-text or map UI: add rows here after manual measurement, or use agent native vision on `screenshots/latest.png` when labels are not OCR-readable.

## Maintenance

1. Discover with EasyOCR (`san5_ocr.py`) or measure on screenshot
2. Verify with fresh capture + `debug -v` (within ~12 px of target)
3. Add or update the table in this skill; set **Status** to `verified`
4. Copy notable lessons to `MEMORY.md` if useful for strategy, not just coords
