---
name: san5-ui
description: >-
  Known UI layouts and button coordinates for Romance of the Three Kingdoms V
  at 1024×768. Use before coordinate click chains, after launch for the CD
  confirm dialog, or to store verified anchors. Discover tentative coords with
  easyocr, then verify and promote rows here.
---

# san5 UI knowledge

Catalog of **verified** screen layouts and click targets. Machine-readable coords live in **`screens.json`** (pretty JSON, one object per screen under `screens`). Narrative procedures and one-off tables stay in this file. Run `skills/mouse/scripts/san5_mouse.py` for clicks.

### `screens.json`

```json
screens.main.buttons["休息"]  →  [940, 215]
screens.main.detect         →  OCR hints that you are on this screen
```

Add new screens under `screens` (e.g. `menu`, `scenario`). Re-verify after resolution changes; promote verified values from EasyOCR or manual measurement.

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

| Label | bbox | click (cx,cy) | Notes |
|-------|------|---------------|-------|
| 開始新遊戲 | 432,308 → 586,338 | **509, 323** | New game |
| 載入遊戲進度 | 418,334 → 598,360 | **508, 347** | Load game |
| 武將單挑 | 446,386 → 572,412 | **509, 399** | Duel mode |

## Scenario selection

| Label | bbox | click (cx,cy) | Notes |
|-------|------|---------------|-------|
| 黃巾之亂 | 510,246 → 598,272 | **554, 259** | Yellow Turban |
| 火燒各陽 | 508,270 → 596,298 | **552, 284** | Burning of Luoyang |
| 臥龍出淵 | 508,348 → 596,374 | **552, 361** | Crouching Dragon |
| 三國鼎立 | 510,374 → 598,400 | **554, 387** | Three Kingdoms |
| 流浪的賢人 | 508,424 → 616,450 | **562, 437** | Wandering Sage |
| 黃巾和南漢 | 510,450 → 618,476 | **564, 463** | Yellow Turban & S.Han |
| 官渡之戰 | 510,476 → 598,502 | **554, 489** | Guandu |
| 星落五丈原 | 508,400 → 616,426 | **562, 413** | Wuzhang Plains |
| 劉備入蜀 | 507,499 → 598,531 | **552, 515** | Liu Bei Enters Shu |

## Ruler selection

| Role | Value | Notes |
|------|-------|-------|
| 決定 (confirm) | **820, 140** | Green confirm, left of 結束 |
| 結束 | **874, 140** | Back/cancel |

Ruler list (right column):

| Label | click (cx,cy) |
|-------|---------------|
| 劉備 | **766, 188** |
| 劉焉 | **766, 222** |
| 董卓 | **867, 222** |
| 袁紹 | **766, 259** |
| 袁術 | **867, 258** |
| 劉表 | **665, 260** |
| 王朗 | **664, 294** |
| 孔融 | **664, 330** |
| 陶謙 | **868, 330** |
| 韓馥 | **664, 366** |
| 喬瑁 | **766, 366** |
| 孔岫 | **869, 366** |
| 新君主 | **662, 402** |

Selected ruler detail: click portrait at **727, 452** to confirm

## Settings screen (after ruler select)

| Setting | click (cx,cy) | Notes |
|---------|---------------|-------|
| 等級 → 高級 | **607, 312** | 初(480, 315)→中(~562)→高(607, 312). Verified 2026-06-04. Click turns selected brown. |
| 不登場/登場 | **623, 340** | Toggle |
| 不觀看/觀看 | **622, 366** | Opening movie toggle |
| 背景音樂 關 | **620, 389** | On/off toggle |
| 音效 關 | **620, 416** | On/off toggle |
| 音量 | **620, 491** | Adjust |
| 決定 (OK/start) | **610, 260** | Below 快定/結束 area, above 虛構 row. Not reliably OCR'd — use this anchor. |

## Game objective screen (勝利條件)

Shown after settings confirm before the main map loads. Has OK/決定 button on the right side.

| Role | Value | Notes |
|------|-------|-------|
| OK / 決定 | **654, 256** | Left half of the right-side button pair (OK + 終了). OCR sees "快定結束" (~0.14 conf). Click center is 654. |
| 終了 (exit) | ~694, 256 | The other button, same row. |

### Procedure

```bash
python3 "$MOUSE" -a move -p 654 256 --sync
# wait for user approval before clicking
python3 "$MOUSE" -a click
```

### Settings procedure (recommended order) (recommended order)

1. **高級** — `move -p 607 312 --sync` → click
2. **不登場** — `move -p 623 340 --sync` → click (if needed)
3. **背景音樂 關** — `move -p 620 389 --sync` → click
4. **音效 關** — `move -p 620 416 --sync` → click
5. **決定** — `move -p 610 260 --sync` → click

Always wait for user confirmation between moves; 決定 is hard for OCR to pick up and was verified manually. Keep the same y=260 height and adjust x if the text anchor drifts.

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

## Main game map (overworld)

Layout: map fills center; top-right has command menu; city labels float on map.

### Top-right: info & stats panel

Vertical column of stats under 君主:

| Label | click (cx,cy) | Notes |
|-------|---------------|-------|
| 君主 (ruler) | **758, 93** | Ruler/governance menu. 3rd in vertical stack. |
| 黃金 (gold) | **759, 144** | Treasury info |
| 軍糧 (grain) | **757, 168** | Military grain supply |

Horizontal row to the right:

| Label | click (cx,cy) | Notes |
|-------|---------------|-------|
| 多謀 (strategists) | **758, 117** | Advisor/strategist list |
| 買糧 (buy grain) | **901, 117** | Grain purchase screen |

### Main command buttons (right column, mid-screen)

Vertical stack along x≈660-680:

| Label | click (cx,cy) | Notes |
|-------|---------------|-------|
| 移動 (move) | **~670, 225** | Troop movement. Top of command list. |
| 戰爭 (war) | **~670, 265** | Declare war / battle. Below 移動. |
| 外交 (diplomacy) | **681, 307** | Diplomatic actions |
| 計謀 (schemes) | **671, 346** | Stratagem/plot/espionage |
| 特殊 (special) | **661, 388** | Special actions |

### Top-right horizontal command bar (y≈215)

Buttons in a single horizontal row at y≈215. See `screens.json` → `screens.main.buttons` for the authoritative list.

| Label | click (cx,cy) |
|-------|---------------|
| 移動 | **650, 215** |
| 戰爭 | **720, 215** |
| 君主 | **760, 215** |
| 擔當 | **810, 215** |
| 情報 | **850, 215** |
| 功能 | **890, 215** |
| 休息 | **940, 215** |

> These are all at the same y=215 height — they're a horizontal bar, not two columns. The earlier "estimated" left/right columns at y≈63-108 and y≈245 were wrong. Use `screens.json` as the single source of truth.

### Cities on map (董卓 火燒各陽 scenario start)

| City | click (cx,cy) | Notes |
|------|---------------|-------|
| 長安 | **357, 327** | Likely 董卓's capital |
| 洛陽 | **502, 326** | Han capital |
| 弘農 | **429, 321** | Between 長安 and 洛陽 |
| 許昌 | **561, 363** | |
| 晉陽 | **545, 158** | Far north |
| 梓潼 | **163, 412** | Shu region |
| 成都 | **92, 459** | Shu region |
| 鄱陽 | **715, 608** | South |
| 桂陽 | **511, 710** | Far south |

## Maintenance

1. Discover with EasyOCR (`san5_ocr.py`) or measure on screenshot
2. Verify with fresh capture + `debug -v` (within ~12 px of target)
3. Add or update the table in this skill; set **Status** to `verified`
4. Copy notable lessons to `MEMORY.md` if useful for strategy, not just coords
