#!/usr/bin/env python3
"""Move and click the mouse inside the DOSBox window on the VNC display.

Coordinates are window-relative (origin top-left), typically 0..1024 x 0..768.
Uses xdotool on the VNC display started by x11vnc_start.sh.

Examples:
  python3 skills/mouse/scripts/san5_mouse.py -a move -p 400 323 --sync
  python3 skills/mouse/scripts/san5_mouse.py -a debug -v
  python3 skills/mouse/scripts/san5_mouse.py -a click
  ./san5_mouse.py -a rclick
  ./san5_mouse.py -a release
  ./san5_mouse.py -a dismiss
  ./san5_mouse.py -a debug -v

Environment:
  SAN5_DISPLAY  X11 display (default :99)
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time

ACTIONS = (
    "move",
    "click",
    "rclick",
    "release",
    "dismiss",
    "debug",
    "show-cursor",
    "hide-cursor",
)
BUTTON = {"click": 1, "rclick": 3, "dismiss": 1}

# san5-dosbox.conf windowresolution; actual X11 window may differ (e.g. 640x400)
LOGICAL_W = int(os.environ.get("SAN5_LOGICAL_WIDTH", "1024"))
LOGICAL_H = int(os.environ.get("SAN5_LOGICAL_HEIGHT", "768"))
CLICK_DELAY_MS = int(os.environ.get("SAN5_CLICK_DELAY_MS", "50"))
# Screen-level mousemove --sync hangs ~15s on Xvfb; window --sync is fast and enough for clicks.
CLICK_SCREEN_SYNC = os.environ.get("SAN5_CLICK_SCREEN_SYNC", "0") == "1"
CLICK_SCREEN_NUDGE = os.environ.get("SAN5_CLICK_SCREEN_NUDGE", "1") == "1"


def _env() -> dict[str, str]:
    env = os.environ.copy()
    env["DISPLAY"] = env.get("SAN5_DISPLAY", ":99")
    env.pop("WAYLAND_DISPLAY", None)
    return env


def _run(*args: str, check: bool = True, verbose: bool = False) -> subprocess.CompletedProcess[str]:
    if verbose:
        print(f"xdotool {' '.join(args)}", file=sys.stderr)
    return subprocess.run(
        ["xdotool", *args],
        env=_env(),
        capture_output=True,
        text=True,
        check=check,
    )


def _parse_shell(stdout: str) -> dict[str, int | str]:
    out: dict[str, int | str] = {}
    for line in stdout.strip().splitlines():
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        try:
            out[key] = int(val)
        except ValueError:
            out[key] = val
    return out


def find_dosbox(wait: bool = True, verbose: bool = False) -> str:
    for attempt in range(40 if wait else 1):
        proc = _run("search", "--name", "DOSBox", check=False, verbose=verbose)
        wins = proc.stdout.strip().splitlines()
        if wins:
            if verbose:
                print(f"found DOSBox window {wins[0]}", file=sys.stderr)
            return wins[0]
        if not wait:
            break
        time.sleep(0.25)
    display = _env()["DISPLAY"]
    print(f"error: DOSBox window not found on {display}", file=sys.stderr)
    print("  is dosbox running?  export SAN5_DISPLAY=:99", file=sys.stderr)
    sys.exit(1)


def window_geometry(win: str, verbose: bool = False) -> tuple[int, int, int, int]:
    proc = _run("getwindowgeometry", "--shell", win, verbose=verbose)
    g = _parse_shell(proc.stdout)
    return int(g["X"]), int(g["Y"]), int(g["WIDTH"]), int(g["HEIGHT"])


def mouse_window_relative(win: str, verbose: bool = False) -> tuple[int, int]:
    win_x, win_y, _, _ = window_geometry(win, verbose=verbose)
    proc = _run("getmouselocation", "--shell", verbose=verbose)
    m = _parse_shell(proc.stdout)
    return int(m["X"]) - win_x, int(m["Y"]) - win_y


def activate(win: str, verbose: bool = False) -> None:
    _run("windowactivate", "--sync", win, check=False, verbose=verbose)


def scale_coords(x: int, y: int, win_w: int, win_h: int, enabled: bool) -> tuple[int, int]:
    if not enabled:
        return x, y
    return x * win_w // LOGICAL_W, y * win_h // LOGICAL_H


def warn_bounds(x: int, y: int, win_w: int, win_h: int) -> None:
    if x < 0 or y < 0 or x >= win_w or y >= win_h:
        print(
            f"warning: ({x}, {y}) outside window 0..{win_w - 1} x 0..{win_h - 1} — clicks may miss",
            file=sys.stderr,
        )


def move_mouse(win: str, x: int, y: int, verbose: bool = False, *, sync_game: bool = False) -> None:
    _run("mousemove", "--window", win, "--sync", str(x), str(y), verbose=verbose)
    if sync_game:
        wake_mouse(win, x, y, verbose=verbose)


def wake_mouse(win: str, x: int, y: int, verbose: bool = False) -> None:
    """Tiny jiggle so DOSBox/SDL gets motion events and redraws the game cursor."""
    if os.environ.get("SAN5_WAKE_CURSOR", "1") == "0":
        return
    for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
        _run("mousemove", "--window", win, str(x + dx), str(y + dy), verbose=verbose)
        time.sleep(0.01)
    _run("mousemove", "--window", win, "--sync", str(x), str(y), verbose=verbose)


def set_x11_cursor(visible: bool, verbose: bool = False) -> None:
    name = "left_ptr" if visible else "none"
    cmd = ["xsetroot", "-display", _env()["DISPLAY"], "-cursor_name", name]
    if verbose:
        print(" ".join(cmd), file=sys.stderr)
    subprocess.run(cmd, check=True)


def cursor_visibility_note() -> None:
    print(
        "cursor visibility on :99:\n"
        "  • X11 arrow is hidden (x11vnc_start.sh) — you will NOT see a black pointer\n"
        "  • x11vnc uses -nocursor — VNC does not overlay a separate pointer\n"
        "  • Only the game's white cursor (drawn inside DOSBox) can appear in the VNC picture\n"
        "  • xdotool warp alone may not redraw it; we jiggle after move (disable: SAN5_WAKE_CURSOR=0)\n"
        "  • VNC app: enable 'remote cursor' / disable 'local cursor only' (see x11vnc_start.sh)\n"
        "  • Debug X11 arrow on host:  -a show-cursor   restore hide:  -a hide-cursor",
        file=sys.stderr,
    )


def screen_coords(win: str, x: int, y: int, verbose: bool = False) -> tuple[int, int]:
    win_x, win_y, _, _ = window_geometry(win, verbose=verbose)
    return win_x + x, win_y + y


def click_mouse(
    win: str,
    x: int,
    y: int,
    button: int = 1,
    verbose: bool = False,
    *,
    move_first: bool = True,
) -> None:
    """mousedown/mouseup at (x,y); optionally move there first."""
    if move_first:
        move_mouse(win, x, y, verbose=verbose)
    time.sleep(CLICK_DELAY_MS / 1000)
    sx, sy = screen_coords(win, x, y, verbose=verbose)
    if CLICK_SCREEN_SYNC:
        _run("mousemove", "--sync", str(sx), str(sy), verbose=verbose)
        time.sleep(0.02)
    elif CLICK_SCREEN_NUDGE:
        _run("mousemove", str(sx), str(sy), verbose=verbose)
        time.sleep(0.03)
    _run("mousedown", str(button), verbose=verbose)
    time.sleep(CLICK_DELAY_MS / 1000)
    _run("mouseup", str(button), verbose=verbose)


def send_key(win: str, *keys: str, verbose: bool = False) -> None:
    _run("key", "--clearmodifiers", "--window", win, *keys, verbose=verbose)


def resolve_target(
    win: str,
    x: int | None,
    y: int | None,
    *,
    dismiss: bool = False,
    verbose: bool = False,
) -> tuple[int, int]:
    _, _, win_w, win_h = window_geometry(win, verbose=verbose)
    if x is not None and y is not None:
        return x, y
    if dismiss:
        return win_w // 2, win_h // 2
    return win_w // 2, win_h // 2


def report(
    win: str,
    x: int,
    y: int,
    verbose: bool = False,
    *,
    scaled_from: tuple[int, int] | None = None,
) -> None:
    win_x, win_y, win_w, win_h = window_geometry(win, verbose=verbose)
    print(f"DOSBox window {win}: {win_w}x{win_h} at screen ({win_x},{win_y})")
    if scaled_from:
        print(f"  scaled {scaled_from[0]}x{scaled_from[1]} ({LOGICAL_W}x{LOGICAL_H}) → ({x}, {y})")
    print(f"  inside window ({x}, {y}) → screen ({win_x + x}, {win_y + y})")
    if (win_w, win_h) != (LOGICAL_W, LOGICAL_H):
        print(
            f"  note: config windowresolution is {LOGICAL_W}x{LOGICAL_H}; "
            f"use --scale if your -p coords are in that space",
            file=sys.stderr,
        )
    warn_bounds(x, y, win_w, win_h)


def parse_position(value: list[int] | None) -> tuple[int | None, int | None]:
    if value is None:
        return None, None
    if len(value) != 2:
        raise argparse.ArgumentTypeError("position requires exactly two integers: X Y")
    return value[0], value[1]


def validate_args(args: argparse.Namespace) -> None:
    x, y = args.x, args.y
    action = args.action

    if action == "move" and (x is None or y is None):
        print("error: -a move requires -p X Y", file=sys.stderr)
        sys.exit(2)

    if action in (
        "click",
        "rclick",
        "release",
        "dismiss",
        "debug",
        "show-cursor",
        "hide-cursor",
    ) and (x is not None or y is not None):
        print(f"error: -a {action} does not take -p (use -a move -p X Y first)", file=sys.stderr)
        sys.exit(2)

    if getattr(args, "sync", False) and action != "move":
        print("error: --sync is only valid with -a move", file=sys.stderr)
        sys.exit(2)


def run_action(args: argparse.Namespace) -> None:
    validate_args(args)
    verbose = args.verbose
    action = args.action

    if action == "debug":
        win = find_dosbox(wait=not args.no_wait, verbose=verbose)
        _, _, win_w, win_h = window_geometry(win, verbose=verbose)
        mx, my = mouse_window_relative(win, verbose=verbose)
        report(win, mx, my, verbose=verbose)
        proc = _run("getmouselocation", verbose=verbose)
        print(proc.stdout.strip())
        print(
            f"DISPLAY={_env()['DISPLAY']}  logical={LOGICAL_W}x{LOGICAL_H}  "
            f"window={win_w}x{win_h}",
            file=sys.stderr,
        )
        print(
            "tips: after -a release, move --sync then click to re-capture; "
            "workflow: move -p X Y --sync, debug -v, click",
            file=sys.stderr,
        )
        cursor_visibility_note()
        if verbose:
            proc = _run("getwindowname", win, verbose=verbose)
            print(f"window name: {proc.stdout.strip()}", file=sys.stderr)
        return

    win = find_dosbox(wait=not args.no_wait, verbose=verbose)
    activate(win, verbose=verbose)
    time.sleep(0.1)

    if action == "show-cursor":
        set_x11_cursor(True, verbose=verbose)
        print(f"X11 pointer visible on {_env()['DISPLAY']} (may still not appear in VNC stream).")
        cursor_visibility_note()
        return

    if action == "hide-cursor":
        set_x11_cursor(False, verbose=verbose)
        print(f"X11 pointer hidden on {_env()['DISPLAY']} (game cursor only).")
        return

    if action == "release":
        send_key(win, "ctrl+F10", verbose=verbose)
        print("DOSBox mouse released (Ctrl+F10).")
        return

    _, _, win_w, win_h = window_geometry(win, verbose=verbose)
    scaled_from: tuple[int, int] | None = None
    raw_x, raw_y = args.x, args.y

    if action == "move":
        x, y = scale_coords(args.x, args.y, win_w, win_h, args.scale)
        if args.scale:
            scaled_from = (args.x, args.y)
        report(win, x, y, verbose=verbose, scaled_from=scaled_from)
        move_mouse(win, x, y, verbose=verbose, sync_game=args.sync)
        sync_note = " (X11→game sync)" if args.sync else ""
        print(f"moved to ({x}, {y}) inside DOSBox window {win}{sync_note}")
        return

    if action in ("click", "rclick"):
        x, y = mouse_window_relative(win, verbose=verbose)
        report(win, x, y, verbose=verbose)
        click_mouse(win, x, y, button=BUTTON[action], verbose=verbose, move_first=False)
        label = "left-clicked" if action == "click" else "right-clicked"
        print(f"{label} at current position ({x}, {y})")
        return

    dismiss = action == "dismiss"
    x, y = resolve_target(win, raw_x, raw_y, dismiss=dismiss, verbose=verbose)
    if not dismiss and raw_x is not None and raw_y is not None:
        sx, sy = scale_coords(raw_x, raw_y, win_w, win_h, args.scale)
        if args.scale:
            scaled_from = (raw_x, raw_y)
        x, y = sx, sy
    report(win, x, y, verbose=verbose, scaled_from=scaled_from)

    click_mouse(win, x, y, button=BUTTON[action], verbose=verbose)

    if action == "dismiss":
        time.sleep(0.25)
        send_key(win, "Return", verbose=verbose)
        print(f"dismissed: clicked ({x}, {y}) and sent Enter")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="DOSBox mouse control on the VNC/Xvfb display.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  %(prog)s -a move -p 400 323 --sync\n"
            "  %(prog)s -a debug -v\n"
            "  %(prog)s -a click\n"
            "  %(prog)s -a rclick\n"
            "  %(prog)s -a release\n"
            "  %(prog)s -a dismiss\n"
            "  %(prog)s -a show-cursor   # debug: X11 arrow on :99\n"
        ),
    )
    p.add_argument(
        "-a",
        "--action",
        required=True,
        choices=ACTIONS,
        metavar="ACTION",
        help="move | click | rclick | release | dismiss | debug | show-cursor | hide-cursor",
    )
    p.add_argument(
        "-p",
        "--position",
        nargs=2,
        type=int,
        metavar=("X", "Y"),
        help="window-relative coordinates (required for move only)",
    )
    p.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="print xdotool commands and extra diagnostics",
    )
    p.add_argument(
        "--no-wait",
        action="store_true",
        help="do not retry if DOSBox window is missing",
    )
    p.add_argument(
        "--scale",
        action="store_true",
        help=f"map -p from logical {LOGICAL_W}x{LOGICAL_H} to actual window size",
    )
    p.add_argument(
        "--sync",
        action="store_true",
        help="with move: jiggle after warp so DOSBox/SDL redraws the game cursor (X11→game)",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.x, args.y = parse_position(args.position)
    try:
        run_action(args)
    except subprocess.CalledProcessError as e:
        print(f"xdotool failed: {e.stderr or e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
