#!/usr/bin/env python3
"""Query san5 screenshots with MiniCPM-V.

Examples:
  python3 skills/minicpm-vision/scripts/minicpm_vision.py -a find --target 開始新遊戲
  python3 skills/minicpm-vision/scripts/minicpm_vision.py -a find --target 確認 --no-capture
  python3 skills/minicpm-vision/scripts/minicpm_vision.py -a find --target 外交 --sync-cursor
  python3 skills/minicpm-vision/scripts/minicpm_vision.py -a ask --prompt "畫面上顯示了什麼？"
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
from pathlib import Path

from analyze_screenshot import (
    DEFAULT_API_BASE,
    DEFAULT_IMAGE,
    DEFAULT_MODEL,
    _to_pixel,
    capture_screenshot,
    chat_completion,
    extract_content,
    get_debug_cursor,
    screen_size,
    wake_cursor_at,
)

ACTIONS = ("find", "ask", "question")
_START_TIME = time.monotonic()


def log(msg: str, *, quiet: bool = False) -> None:
    if quiet:
        return
    elapsed = time.monotonic() - _START_TIME
    print(f"[minicpm-find {elapsed:5.1f}s] {msg}", file=sys.stderr, flush=True)


def show_model_reply(text: str) -> None:
    print("--- MiniCPM-V reply ---", file=sys.stderr)
    print(text, file=sys.stderr)
    print("-----------------------", file=sys.stderr)


def show_model_prompt(text: str) -> None:
    print("--- MiniCPM-V prompt ---", file=sys.stderr)
    print(text, file=sys.stderr)
    print("------------------------", file=sys.stderr)


def parse_bbox(text: str, *, w: int, h: int) -> list[int] | None:
    values = [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", text)]
    if len(values) < 4:
        return None
    x1 = _to_pixel(values[0], w)
    y1 = _to_pixel(values[1], h)
    x2 = _to_pixel(values[2], w)
    y2 = _to_pixel(values[3], h)
    left, right = sorted((x1, x2))
    top, bottom = sorted((y1, y2))
    if left == right or top == bottom:
        return None
    return [left, top, right, bottom]


def bbox_center(bbox: list[int]) -> list[int]:
    x1, y1, x2, y2 = bbox
    return [(x1 + x2) // 2, (y1 + y2) // 2]


def point_in_bbox(point: list[int] | None, bbox: list[int]) -> bool | None:
    if point is None:
        return None
    x, y = point
    x1, y1, x2, y2 = bbox
    return x1 <= x <= x2 and y1 <= y <= y2


def require_api_key() -> str | None:
    api_key = os.environ.get("MODELBEST_API_KEY")
    if api_key:
        return api_key
    print(
        "error: set MODELBEST_API_KEY (see skills/minicpm-vision/SKILL.md)",
        file=sys.stderr,
    )
    return None


def prepare_image(args: argparse.Namespace, *, need_cursor: bool) -> tuple[str, list[int] | None] | None:
    image_path = args.image
    cursor = get_debug_cursor(quiet=args.quiet) if need_cursor else None

    if args.capture:
        if args.sync_cursor and cursor:
            wake_cursor_at(cursor[0], cursor[1], quiet=args.quiet)
        log(f"capturing screenshot -> {image_path}", quiet=args.quiet)
        capture_screenshot(image_path, quiet=args.quiet)
    elif not Path(image_path).is_file():
        print(f"error: image not found: {image_path}", file=sys.stderr)
        print("hint: omit --no-capture to grab a fresh screenshot", file=sys.stderr)
        return None

    return image_path, cursor


def request_prompt(args: argparse.Namespace, prompt: str) -> tuple[dict, str] | None:
    api_key = require_api_key()
    if not api_key:
        return None

    try:
        data = chat_completion(
            api_base=args.api_base,
            api_key=api_key,
            model=args.model,
            prompt=prompt,
            image_path=args.image,
            timeout=args.timeout,
            quiet=args.quiet,
        )
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"error: HTTP {e.code}: {body}", file=sys.stderr)
        return None
    except urllib.error.URLError as e:
        print(f"error: {e.reason}", file=sys.stderr)
        return None

    return data, extract_content(data).strip()


def find_target(args: argparse.Namespace) -> int:
    prepared = prepare_image(args, need_cursor=True)
    if prepared is None:
        return 1
    image_path, cursor = prepared

    model_prompt = f"""请找出游戏画面中 "{args.target}" 按钮的精确位置。

游戏分辨率是 1024x768
返回按钮中心的坐标，格式为 (X1, Y1, X2, Y2)


重要：只返回坐标，不要有其他文字。"""

    log(f'asking MiniCPM-V for "{args.target}"', quiet=args.quiet)
    if args.verbose:
        show_model_prompt(model_prompt)
    requested = request_prompt(args, model_prompt)
    if requested is None:
        return 1
    _data, content = requested
    if args.verbose:
        show_model_reply(content)
    bbox = parse_bbox(content, w=screen_size()[0], h=screen_size()[1])
    if bbox is None:
        print(f"error: could not parse bbox from MiniCPM-V response: {content!r}", file=sys.stderr)
        return 1

    result = {
        "action": "find",
        "target": args.target,
        "image": image_path,
        "bbox": bbox,
        "center": bbox_center(bbox),
        "cursor": cursor,
        "cursor_in_bbox": point_in_bbox(cursor, bbox),
    }
    if args.raw:
        result["raw_response"] = content
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def ask_question(args: argparse.Namespace) -> int:
    prepared = prepare_image(args, need_cursor=args.sync_cursor)
    if prepared is None:
        return 1
    image_path, _cursor = prepared

    log("asking MiniCPM-V custom question", quiet=args.quiet)
    if args.verbose:
        show_model_prompt(args.prompt)
    requested = request_prompt(args, args.prompt)
    if requested is None:
        return 1
    data, content = requested

    if args.verbose:
        show_model_reply(content)

    if args.raw:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0

    print(content)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Find buttons or ask MiniCPM-V questions about a san5 screenshot.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  %(prog)s -a find --target 開始新遊戲\n"
            "  %(prog)s -a find --target 確認 --no-capture -v\n"
            "  %(prog)s -a find --target 外交 --sync-cursor\n"
            '  %(prog)s -a ask --prompt "畫面上顯示了什麼？"\n'
            '  %(prog)s -a question --prompt "滑鼠是不是在按鈕上？"\n'
        ),
    )
    p.add_argument(
        "-a",
        "--action",
        required=True,
        choices=ACTIONS,
        metavar="ACTION",
        help="find | ask | question",
    )
    p.add_argument(
        "--target",
        help="button label to locate in the current game screen",
    )
    p.add_argument(
        "--prompt",
        help="custom question to send to MiniCPM-V (used by ask/question)",
    )
    p.add_argument(
        "image",
        nargs="?",
        default=DEFAULT_IMAGE,
        help=f"screenshot path to read/write (default: {DEFAULT_IMAGE})",
    )
    p.add_argument(
        "--capture",
        dest="capture",
        action="store_true",
        default=True,
        help="capture a fresh screenshot before sending it to MiniCPM-V (default)",
    )
    p.add_argument(
        "--no-capture",
        dest="capture",
        action="store_false",
        help="reuse an existing screenshot file instead of capturing a new one",
    )
    p.add_argument(
        "--sync-cursor",
        action="store_true",
        help="before capture, run dosbox_mouse move --sync at the current cursor position",
    )
    p.add_argument("--model", default=os.environ.get("MODELBEST_MODEL", DEFAULT_MODEL))
    p.add_argument(
        "--api-base",
        default=os.environ.get("MODELBEST_API_BASE", DEFAULT_API_BASE),
    )
    p.add_argument(
        "--timeout",
        type=float,
        default=float(os.environ.get("MODELBEST_TIMEOUT", "120")),
    )
    p.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="print the prompt sent and raw MiniCPM-V reply to stderr",
    )
    p.add_argument(
        "--quiet",
        action="store_true",
        help="suppress progress logs on stderr",
    )
    p.add_argument(
        "--raw",
        action="store_true",
        help="print raw API JSON for ask/question, or include raw model text in find JSON",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    global _START_TIME
    _START_TIME = time.monotonic()
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.action == "find":
        if not args.target:
            print("error: -a find requires --target BUTTON_NAME", file=sys.stderr)
            return 2
        return find_target(args)
    if args.action in {"ask", "question"}:
        if not args.prompt:
            print("error: -a ask requires --prompt TEXT", file=sys.stderr)
            return 2
        return ask_question(args)
    print(f"error: unsupported action: {args.action}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
