---
name: san5-ui
description: >-
  Known UI layouts and button coordinates for Romance of the Three Kingdoms V
  at 1024×768. Use before coordinate click chains, after launch for the CD
  confirm dialog, or when vision needs verified anchor points for san5 screens.
---

# san5 UI knowledge

Markdown-only catalog of **verified** screen layouts and click targets. No scripts in this skill — read coords here, then run `skills/dosbox-mouse/scripts/dosbox_mouse.py` (or vision scripts to discover unknown UI).

## Coordinate system

- Image / window size: **1024×768**, origin **(0, 0)** top-left
- DOSBox pinned at **(0, 0)** on display `:99` (see `san5-starter`, `TOOLS.md`)
- `(x1,y1)` = bbox top-left; `(x2,y2)` = bottom-right; click = center unless noted
- Re-verify after resolution or layout changes; promote tentative finds from `MEMORY.md` into this file

## first_cd_confirm

First dialog after splash: CD-ROM / 確認 prompt. DOSBox does not accept clicks until the pointer is **captured** once inside the window.

| Role | Value | Notes |
|------|-------|-------|
| Wait before acting | ~3 s | After splash Enter keys; use vision if unsure |
| Capture point (dialog body) | **512, 384** | First `move --sync` + `click` to grab mouse |
| 確認 bbox | **432, 398** → **592, 422** | top-left → bottom-right |
| 確認 click center | **512, 410** | `(432+592)/2`, `(398+422)/2` |

### Procedure

From workspace root (`MOUSE=skills/dosbox-mouse/scripts/dosbox_mouse.py`):

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

See `skills/dosbox-mouse/SKILL.md` for sync vs capture vs release.

### Overrides

Pass different pixels by editing commands above, or export before each run:

- `SAN5_CAPTURE_X` / `SAN5_CAPTURE_Y` — capture point (default 512, 384)
- `SAN5_CONFIRM_X1` … `SAN5_CONFIRM_Y2` — bbox corners (defaults 432,398,592,422)

## Main menu

*(Add rows here after verification with `debug -v` or vision + confirm.)*

| Label | bbox (x1,y1,x2,y2) | click (cx,cy) | Notes |
|-------|---------------------|---------------|-------|
| — | — | — | use minicpm-vision or native vision to discover |

## Maintenance

1. Verify with screenshot + `debug -v` (within ~12 px of target)
2. Add or update the table in this skill
3. Copy notable lessons to `MEMORY.md` if useful for strategy, not just coords
