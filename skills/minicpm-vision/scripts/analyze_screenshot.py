#!/usr/bin/env python3
"""Send a san5 screenshot to ModelBest MiniCPM-V and print vision-click analysis.

Examples:
  export MODELBEST_API_KEY=sk-...
  python3 skills/minicpm-vision/scripts/analyze_screenshot.py --capture
  python3 skills/minicpm-vision/scripts/analyze_screenshot.py san5_screenshot.png
  python3 skills/minicpm-vision/scripts/analyze_screenshot.py -o analysis.md
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import subprocess
import sys
import urllib.error
import urllib.request

DEFAULT_API_BASE = "https://api.modelbest.cn/v1"
DEFAULT_MODEL = "MiniCPM-V-4.6-Instruct"
DEFAULT_IMAGE = "san5_screenshot.png"

SAN5_VISION_PROMPT = """You are analyzing a screenshot of Romance of the Three Kingdoms V (三国志V) running in DOSBox.

Image size is exactly 1024×768 pixels. Origin (0,0) is the top-left corner. All coordinates must be in this pixel space.

Identify clickable UI elements (buttons, menu items, dialog choices). For each target give a tight bounding box (x1,y1,x2,y2) where (x1,y1) is top-left and (x2,y2) is bottom-right. Compute click center: cx=(x1+x2)//2, cy=(y1+y2)//2.

Respond ONLY in this markdown template (fill every section; use "none" if empty):

## Screen
- type: dialog | main_menu | map | battle | other
- summary: one line

## Message
- text: (dialog or status text, or none)

## Targets
| label | bbox (x1,y1,x2,y2) | click (cx,cy) |
|-------|---------------------|---------------|
| (rows for each button) |

## Next action
- click: (label of the best next button, or none)
"""


def image_data_url(path: str) -> str:
    mime, _ = mimetypes.guess_type(path)
    if not mime or not mime.startswith("image/"):
        mime = "image/png"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def capture_screenshot(path: str) -> None:
    display = os.environ.get("SAN5_DISPLAY", ":99")
    w = os.environ.get("SAN5_SCREEN_WIDTH", "1024")
    h = os.environ.get("SAN5_SCREEN_HEIGHT", "768")
    region = f"0,0,{w},{h}"
    cmd = ["scrot", "-D", display, "-a", region, path]
    print("$", " ".join(cmd), file=sys.stderr)
    subprocess.run(cmd, check=True)


def chat_completion(
    *,
    api_base: str,
    api_key: str,
    model: str,
    prompt: str,
    image_path: str,
    timeout: float,
) -> dict:
    url = f"{api_base.rstrip('/')}/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": image_data_url(image_path)},
                    },
                ],
            }
        ],
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def extract_content(data: dict) -> str:
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise ValueError(f"unexpected API response: {data!r}") from e


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Analyze a san5 PNG with ModelBest MiniCPM-V (vision workaround)."
    )
    p.add_argument(
        "image",
        nargs="?",
        default=DEFAULT_IMAGE,
        help=f"PNG path (default: {DEFAULT_IMAGE})",
    )
    p.add_argument(
        "--capture",
        action="store_true",
        help="run scrot before analysis (see skills/screenshot)",
    )
    p.add_argument("-o", "--output", help="write analysis markdown to this file")
    p.add_argument("--prompt", help="override the default san5 vision prompt")
    p.add_argument("--model", default=os.environ.get("MODELBEST_MODEL", DEFAULT_MODEL))
    p.add_argument(
        "--api-base",
        default=os.environ.get("MODELBEST_API_BASE", DEFAULT_API_BASE),
    )
    p.add_argument(
        "--timeout",
        type=float,
        default=float(os.environ.get("MODELBEST_TIMEOUT", "300")),
    )
    p.add_argument("--raw", action="store_true", help="print full JSON response")
    args = p.parse_args(argv)

    api_key = os.environ.get("MODELBEST_API_KEY")
    if not api_key:
        print(
            "error: set MODELBEST_API_KEY (see skills/minicpm-vision/SKILL.md)",
            file=sys.stderr,
        )
        return 1

    image_path = args.image
    if args.capture:
        capture_screenshot(image_path)
    elif not os.path.isfile(image_path):
        print(f"error: image not found: {image_path}", file=sys.stderr)
        print("hint: run with --capture or scrot first", file=sys.stderr)
        return 1

    prompt = args.prompt or SAN5_VISION_PROMPT
    try:
        data = chat_completion(
            api_base=args.api_base,
            api_key=api_key,
            model=args.model,
            prompt=prompt,
            image_path=image_path,
            timeout=args.timeout,
        )
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"error: HTTP {e.code}: {body}", file=sys.stderr)
        return 1
    except urllib.error.URLError as e:
        print(f"error: {e.reason}", file=sys.stderr)
        return 1

    if args.raw:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0

    content = extract_content(data)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(content)
            if not content.endswith("\n"):
                f.write("\n")
        print(f"wrote {args.output}", file=sys.stderr)
    else:
        print(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
