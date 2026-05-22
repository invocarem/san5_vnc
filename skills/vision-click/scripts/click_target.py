#!/usr/bin/env python3
"""Click inside a bbox using dosbox_mouse (window-relative coords).

Examples:
  python3 click_target.py --bbox 528 495 654 514
  python3 click_target.py --point 591 505
  python3 click_target.py --bbox 528 495 654 514 --dry-run
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

LOGICAL_W = int(os.environ.get("SAN5_LOGICAL_WIDTH", "800"))
LOGICAL_H = int(os.environ.get("SAN5_LOGICAL_HEIGHT", "600"))


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


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Click a vision target inside DOSBox.")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--bbox", nargs=4, type=int, metavar=("X1", "Y1", "X2", "Y2"))
    g.add_argument("--point", nargs=2, type=int, metavar=("X", "Y"))
    p.add_argument("--move-only", action="store_true", help="move without click")
    p.add_argument("--dry-run", action="store_true", help="print coords only")
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

    action = "move" if args.move_only else "click"
    cmd = ["python3", mouse_script(), "-a", action, "-p", str(x), str(y)]
    if args.verbose:
        cmd.append("-v")

    print(f"target=({x}, {y}) action={action}")
    if args.dry_run:
        print(" ".join(cmd))
        return 0

    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
