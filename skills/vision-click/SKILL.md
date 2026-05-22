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

1. **Capture** — read `skills/screenshot/SKILL.md`, then:

   ```bash
   ./skills/screenshot/scripts/san5_capture.sh san5_screenshot.png
   ```

2. **Analyze** — open the PNG and identify:
   - **Buttons** — label, bounding box in image pixels `(x1, y1, x2, y2)` top-left origin
   - **Messages** — dialog text, blocking prompts
   - **Game state** — screen type (map, menu, battle, dialog), faction/turn if visible

   Coordinates are in **PNG pixel space** from the cropped capture (usually ≈800×600). If capture stdout shows `image_height` ≠ `height`, scale Y (and X if needed) to window space before clicking (see screenshot skill).

3. **Click** — pick a point **inside** the button bbox before clicking:
   - Prefer bbox **center**: `cx = (x1+x2)//2`, `cy = (y1+y2)//2`
   - Do not click on borders or outside the bbox
   - Confirm DOSBox is running; run `dosbox_mouse.py -a debug` if clicks miss

   ```bash
   python3 skills/vision-click/scripts/click_target.py --bbox X1 Y1 X2 Y2
   python3 skills/vision-click/scripts/click_target.py --point X Y
   python3 skills/vision-click/scripts/click_target.py --bbox X1 Y1 X2 Y2 --dry-run
   ```

   Or directly:

   ```bash
   python3 skills/dosbox-mouse/scripts/dosbox_mouse.py -a move -p CX CY
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
| 確認  | 528,495,654,514     | 591,504       |

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
| Click | `dosbox-mouse` |

See `TOOLS.md` for display `:99` and VNC port.

## Safety

- Do not click blindly: always tie coordinates to a visible bbox from the current screenshot
- After `release`, run `-a grab` before more clicks (`dosbox-mouse`)
- If window size ≠ 800×600, use `dosbox_mouse.py --scale` (see dosbox-mouse skill)

## Troubleshooting

| Problem | What to try |
|---------|-------------|
| Wrong button | Re-capture; tighten bbox; click center |
| Clicks miss | `-a debug`; check capture used cropped window script |
| Stale screen | Capture again after each click |
| No DOSBox | Start game; confirm `SAN5_DISPLAY=:99` |
