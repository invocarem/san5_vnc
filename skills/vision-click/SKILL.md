---
name: vision-click
description: >-
  Capture san5, analyze the screenshot with vision for buttons and game state,
  then click targets inside DOSBox using window-relative coordinates. Use for
  vision-driven play, finding UI elements, or automated clicks on dialogs/menus.
---

# san5 vision-click

End-to-end: **screenshot → vision → click inside target**.

## Workflow

1. **Capture** — `scrot` on `:99` (see `skills/screenshot/SKILL.md`):

   ```bash
   scrot -D :99 -a 0,0,1024,768 san5_screenshot.png
   ```

2. **Analyze** — open the PNG and identify (or use `skills/minicpm-vision` if the agent has **no native vision**):

   ```bash
   export MODELBEST_API_KEY=sk-...   # see minicpm-vision/SKILL.md (public trial key)
   python3 skills/minicpm-vision/scripts/analyze_screenshot.py --capture
   ```

   With native vision, open the PNG and identify:
   - **Buttons** — label, bounding box in image pixels `(x1, y1, x2, y2)` top-left origin
   - **Messages** — dialog text, blocking prompts
   - **Game state** — screen type (map, menu, battle, dialog), faction/turn if visible

   Coordinates are **PNG pixel space** (1024×768, same as `dosbox_mouse -p`).

3. **Click** — center of button bbox: `cx = (x1+x2)//2`, `cy = (y1+y2)//2`

   **First screen (確認 / CD dialog)** — DOSBox has not captured the mouse yet (`autolock=false`). A single `click -p` on the button often does nothing. Use **capture → move → grab**:

   ```bash
   # on launch (default): san5_start.sh runs mouse sync when SAN5_MOUSE_SYNC=1
   # manual / re-run:
   python3 skills/vision-click/scripts/click_target.py --bbox 432 398 592 422 --first-dialog
   ```

   Manual equivalent:

   ```bash
   python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a click -p 512 384   # capture (dialog body)
   python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a move  -p 512 410   # over 確認
   python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a grab              # click button
   ```

   **Later screens** (mouse already in DOSBox):

   ```bash
   python3 skills/vision-click/scripts/click_target.py --bbox X1 Y1 X2 Y2
   python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a click -p CX CY
   ```

4. **Verify** — capture again or describe the new screen; retry if the dialog is still open.

## Vision output template

After analyzing the screenshot, record:

```markdown
## Screen
- type: dialog | main_menu | map | battle | other
- summary: one line

## Message
- text: (if any)

## Targets
| label | bbox (x1,y1,x2,y2) | click (cx,cy) |
|-------|---------------------|---------------|
| 確認  | 432,398,592,422     | 512,410       |

## Next action
- click: 確認
```

Rules for bboxes:

- `(x1,y1)` top-left, `(x2,y2)` bottom-right, exclusive max edge ok
- `click` must satisfy `x1 <= cx < x2` and `y1 <= cy < y2`
- If unsure, use a smaller inner bbox and center that

## Prerequisites

| Step | Skill / tool |
|------|----------------|
| VNC + game | `san5-runtime` |
| Capture | `screenshot` (`scrot`, `xdotool`) |
| No native vision | `minicpm-vision` (`analyze_screenshot.py`) |
| Click | `dosbox-mouse` |

See `TOOLS.md` for display `:99` and VNC port.

## Safety

- Do not click blindly: always tie coordinates to a visible bbox from the current screenshot
- After `release`, run `-a grab` before more clicks (`dosbox-mouse`)
- If using old 800×600 notes, use `dosbox_mouse.py --scale` or re-capture at 1024×768

## Troubleshooting

| Problem | What to try |
|---------|-------------|
| Wrong button | Re-capture; tighten bbox; click center |
| Clicks miss / first dialog | `--first-dialog` or capture→move→grab; `-a debug` |
| Stale screen | Capture again after each click |
| No DOSBox | Start game; confirm `SAN5_DISPLAY=:99` |
