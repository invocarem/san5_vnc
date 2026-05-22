#!/usr/bin/env python3
"""Click inside a bbox using dosbox_mouse (window-relative coords).

Examples:
  python3 click_target.py --bbox 432 398 592 422
  python3 click_target.py --point 512 410
  python3 click_target.py --bbox 432 398 592 422 --first-dialog
  python3 click_target.py --bbox 432 398 592 422 --dry-run
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time

LOGICAL_W = int(os.environ.get("SAN5_LOGICAL_WIDTH", "1024"))
LOGICAL_H = int(os.environ.get("SAN5_LOGICAL_HEIGHT", "768"))
CAPTURE_X = int(os.environ.get("SAN5_CAPTURE_X", str(LOGICAL_W // 2)))
CAPTURE_Y = int(os.environ.get("SAN5_CAPTURE_Y", str(LOGICAL_H // 2 - 80)))


def center_in_bbox(x1: int, y1: int, x2: int, y2: int) -> tuple[int, int]:
    if x1 > x2:
        x1, x2 = x2, x1
    if y1 > y2:
        y1, y2 = y2, y1
    if x2 <= x1 or y2 <= y1:
        raise ValueError(f"degenerate bbox: ({x1},{y1})-({x2},{y2})")
    cx = (x1 + x2) // 2
    cy = (y1 + y2) // 2
    if not (x1 <= cx < x2 and y1 <= cy < y2):
        raise ValueError(f"center ({cx},{cy}) outside bbox")
    return cx, cy


def clamp_logical(x: int, y: int) -> tuple[int, int]:
    x = max(0, min(x, LOGICAL_W - 1))
    y = max(0, min(y, LOGICAL_H - 1))
    return x, y


def mouse_script() -> str:
    return os.environ.get(
        "SAN5_MOUSE_SCRIPT",
        "skills/dosbox-mouse/scripts/dosbox_mouse.py",
    )


def run_mouse(
    action: str,
    x: int | None = None,
    y: int | None = None,
    *,
    verbose: bool = False,
    dry_run: bool = False,
) -> int:
    cmd = ["python3", mouse_script(), "-a", action]
    if x is not None and y is not None:
        cmd.extend(["-p", str(x), str(y)])
    if verbose:
        cmd.append("-v")
    print("$", " ".join(cmd))
    if dry_run:
        return 0
    return subprocess.call(cmd)


def first_dialog_click(
    x: int,
    y: int,
    *,
    verbose: bool = False,
    dry_run: bool = False,
) -> int:
    """Capture mouse in DOSBox, move to target, grab-click on button."""
    cap_x, cap_y = clamp_logical(CAPTURE_X, CAPTURE_Y)
    print(f"first-dialog: capture click ({cap_x},{cap_y}) → move ({x},{y}) → grab")
    steps: list[tuple[str, int | None, int | None, float]] = [
        ("click", cap_x, cap_y, 0.3),
        ("move", x, y, 0.15),
        ("grab", None, None, 0.0),
    ]
    for action, sx, sy, delay in steps:
        rc = run_mouse(action, sx, sy, verbose=verbose, dry_run=dry_run)
        if rc != 0:
            return rc
        if delay and not dry_run:
            time.sleep(delay)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Click a vision target inside DOSBox.")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--bbox", nargs=4, type=int, metavar=("X1", "Y1", "X2", "Y2"))
    g.add_argument("--point", nargs=2, type=int, metavar=("X", "Y"))
    p.add_argument(
        "--first-dialog",
        action="store_true",
        help="CD/確認 screen: capture click, move to target, grab (DOSBox not capturing mouse yet)",
    )
    p.add_argument("--move-only", action="store_true", help="move without click")
    p.add_argument("--dry-run", action="store_true", help="print commands only")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)

    if args.bbox:
        x, y = center_in_bbox(*args.bbox)
    else:
        x, y = args.point[0], args.point[1]

    x, y = clamp_logical(x, y)
    if args.bbox:
        x1, y1, x2, y2 = args.bbox
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        if not (x1 <= x < x2 and y1 <= y < y2):
            print(
                f"warning: ({x},{y}) not inside bbox ({x1},{y1})-({x2},{y2}) after clamp",
                file=sys.stderr,
            )

    print(f"target=({x}, {y})")
    if args.first_dialog:
        return first_dialog_click(x, y, verbose=args.verbose, dry_run=args.dry_run)

    action = "move" if args.move_only else "click"
    return run_mouse(action, x, y, verbose=args.verbose, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
