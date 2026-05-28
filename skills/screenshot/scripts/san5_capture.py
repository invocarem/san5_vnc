#!/usr/bin/env python3
"""Capture the san5 framebuffer to a PNG (see skills/screenshot/SKILL.md).

Examples:
  python3 skills/screenshot/scripts/san5_capture.py
  SAN5_RUN=run2 python3 skills/screenshot/scripts/san5_capture.py
  python3 skills/screenshot/scripts/san5_capture.py --new-run
  python3 skills/screenshot/scripts/san5_capture.py screenshots/archive/menu.png

Environment:
  SAN5_RUN                 Run folder name (default: run1)
  SAN5_SCREENSHOTS_DIR     Base directory (default: screenshots)
  SAN5_DISPLAY             X display for scrot (default: :99)
  SAN5_SCREEN_WIDTH        Capture width (default: 1024)
  SAN5_SCREEN_HEIGHT       Capture height (default: 768)
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_RUN = "run1"
SEQ_RE = re.compile(r"^0*(\d+)$")
RUN_RE = re.compile(r"^run0*(\d+)$")


def workspace_root() -> Path:
    return Path(__file__).resolve().parents[3]


def next_seq_in_run(run_dir: Path) -> str:
    max_n = 0
    if run_dir.is_dir():
        for path in run_dir.glob("*.png"):
            m = SEQ_RE.match(path.stem)
            if m:
                max_n = max(max_n, int(m.group(1)))
    return f"{max_n + 1:03d}"


def next_run_name(screenshots_dir: Path) -> str:
    max_n = 0
    if screenshots_dir.is_dir():
        for path in screenshots_dir.iterdir():
            if not path.is_dir():
                continue
            m = RUN_RE.match(path.name)
            if m:
                max_n = max(max_n, int(m.group(1)))
    if max_n == 0:
        return DEFAULT_RUN
    return f"run{max_n + 1}"


def resolve_output(
    screenshots_dir: Path,
    explicit: Path | None,
    run: str | None,
    new_run: bool,
) -> tuple[Path, bool]:
    """Return (output path, update_latest)."""
    if explicit is not None:
        return explicit, False

    if new_run:
        run_name = next_run_name(screenshots_dir)
    else:
        run_name = run or os.environ.get("SAN5_RUN", DEFAULT_RUN)

    run_dir = screenshots_dir / run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    seq = next_seq_in_run(run_dir)
    return run_dir / f"{seq}.png", True


def capture(image: Path, display: str, width: int, height: int) -> None:
    image.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["DISPLAY"] = display
    env.pop("WAYLAND_DISPLAY", None)
    region = f"0,0,{width},{height}"
    print(f"[san5] capture -> {image}", file=sys.stderr)
    subprocess.run(
        ["scrot", "-D", display, "-a", region, str(image)],
        env=env,
        check=True,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture the san5 framebuffer with scrot.",
    )
    parser.add_argument(
        "output",
        nargs="?",
        help="Explicit output PNG (bypasses run layout; does not update latest.png)",
    )
    parser.add_argument(
        "--run",
        metavar="NAME",
        help="Run folder for this capture (overrides SAN5_RUN)",
    )
    parser.add_argument(
        "--new-run",
        action="store_true",
        help="Use the next run folder (run2, run3, …)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    os.chdir(workspace_root())

    screenshots_dir = Path(os.environ.get("SAN5_SCREENSHOTS_DIR", "screenshots"))
    latest = screenshots_dir / "latest.png"
    display = os.environ.get("SAN5_DISPLAY", ":99")
    width = int(os.environ.get("SAN5_SCREEN_WIDTH", "1024"))
    height = int(os.environ.get("SAN5_SCREEN_HEIGHT", "768"))

    explicit = Path(args.output) if args.output else None
    image, update_latest = resolve_output(
        screenshots_dir,
        explicit,
        args.run,
        args.new_run,
    )

    try:
        capture(image, display, width, height)
    except FileNotFoundError:
        print("san5_capture: scrot not found", file=sys.stderr)
        return 127
    except subprocess.CalledProcessError as exc:
        return exc.returncode

    if update_latest:
        shutil.copy2(image, latest)
        print(f"[san5] latest -> {latest} (from {image})", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
