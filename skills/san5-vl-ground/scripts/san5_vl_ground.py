#!/usr/bin/env python3
"""Capture (optional) and ground a san5 screenshot via Qwen3-VL Grounding API.

Examples:
  uv run --group san5-vl-ground python skills/san5-vl-ground/scripts/san5_vl_ground.py --json
  uv run --group san5-vl-ground python skills/san5-vl-ground/scripts/san5_vl_ground.py --json --match 確認
  uv run --group san5-vl-ground python skills/san5-vl-ground/scripts/san5_vl_ground.py --json --ground-path

Environment:
  SAN5_GROUND_BASE_URL   Server root (default: http://127.0.0.1:5080)
  SAN5_GROUND_PROMPT     Override default grounding prompt
  SAN5_SCREENSHOT        Default PNG after capture (default: screenshots/latest.png)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

DEFAULT_IMAGE = os.environ.get("SAN5_SCREENSHOT", "screenshots/latest.png")
DEFAULT_BASE_URL = os.environ.get("SAN5_GROUND_BASE_URL", "http://127.0.0.1:5080")
# The server internally resizes images to a square processing resolution
# (default 1000x1000). The returned bbox coordinates are in that space.
# This env var lets you override it.
PROC_W = int(os.environ.get("SAN5_GROUND_PROC_W", "1000"))
PROC_H = int(os.environ.get("SAN5_GROUND_PROC_H", "1000"))
DEFAULT_PROMPT = os.environ.get(
    "SAN5_GROUND_PROMPT",
    "Detect all clickable UI elements in this Romance of the Three Kingdoms V game screenshot "
    "(buttons, menu items, dialog actions). Return a JSON array with 'label' and 'bbox_2d' for each.",
)

OCR_SCRIPTS = Path(__file__).resolve().parents[2] / "easyocr/scripts"
if str(OCR_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(OCR_SCRIPTS))

import san5_ocr  # noqa: E402

OcrTarget = san5_ocr.OcrTarget
workspace_root = san5_ocr.workspace_root
run_capture = san5_ocr.run_capture
screen_size = san5_ocr.screen_size
clamp = san5_ocr.clamp
find_match = san5_ocr.find_match
summary_line = san5_ocr.summary_line
describe_targets = san5_ocr.describe_targets


def build_match_prompt(match: str | None, extra: str | None) -> str:
    prompt = DEFAULT_PROMPT
    if match:
        prompt += f" Pay special attention to elements matching: {match!r}."
    if extra:
        prompt += f" {extra}"
    return prompt


def scale_bbox(
    bbox: list[int],
    *,
    src_width: int,
    src_height: int,
    dst_width: int,
    dst_height: int,
) -> list[int]:
    if src_width == dst_width and src_height == dst_height:
        return bbox
    if src_width <= 0 or src_height <= 0:
        return bbox

    sx = dst_width / src_width
    sy = dst_height / src_height
    x1, y1, x2, y2 = bbox
    return [
        clamp(int(round(x1 * sx)), 0, dst_width - 1),
        clamp(int(round(y1 * sy)), 0, dst_height - 1),
        clamp(int(round(x2 * sx)), 0, dst_width - 1),
        clamp(int(round(y2 * sy)), 0, dst_height - 1),
    ]


def detection_to_target(
    det: dict[str, Any],
    *,
    src_width: int,
    src_height: int,
    dst_width: int,
    dst_height: int,
) -> OcrTarget | None:
    label = str(det.get("label", "")).strip()
    if not label:
        return None

    bbox = det.get("bbox_pixels")
    if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
        bbox = det.get("bbox_2d")
    if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
        return None

    try:
        x1, y1, x2, y2 = (int(round(float(v))) for v in bbox)
    except (TypeError, ValueError):
        return None

    scaled = scale_bbox(
        [x1, y1, x2, y2],
        src_width=src_width,
        src_height=src_height,
        dst_width=dst_width,
        dst_height=dst_height,
    )
    x1, y1, x2, y2 = scaled
    if x2 <= x1 or y2 <= y1:
        return None

    center = det.get("center_pixels")
    if isinstance(center, (list, tuple)) and len(center) == 2:
        try:
            cx = int(round(float(center[0]) * (dst_width / src_width if src_width else 1)))
            cy = int(round(float(center[1]) * (dst_height / src_height if src_height else 1)))
            click = [
                clamp(cx, x1, x2),
                clamp(cy, y1, y2),
            ]
        except (TypeError, ValueError):
            click = [(x1 + x2) // 2, (y1 + y2) // 2]
    else:
        click = [(x1 + x2) // 2, (y1 + y2) // 2]

    conf_raw = det.get("confidence", det.get("score", 0.9))
    try:
        confidence = float(conf_raw)
    except (TypeError, ValueError):
        confidence = 0.9
    confidence = max(0.0, min(1.0, confidence))

    return OcrTarget(
        label=label,
        bbox=[x1, y1, x2, y2],
        click=click,
        confidence=round(confidence, 4),
    )


def targets_from_ground_response(data: dict[str, Any]) -> list[OcrTarget]:
    dst_width, dst_height = screen_size()
    size = data.get("image_size") if isinstance(data.get("image_size"), dict) else {}
    src_width = int(size.get("width", 0))
    src_height = int(size.get("height", 0))
    # If the server didn't return image_size, it likely resized internally
    # to a processing resolution (default 1000x1000). Get it from env.
    if src_width <= 0 or src_height <= 0:
        src_width = PROC_W
        src_height = PROC_H

    detections = data.get("detections")
    if not isinstance(detections, list):
        return []

    targets: list[OcrTarget] = []
    for det in detections:
        if not isinstance(det, dict):
            continue
        target = detection_to_target(
            det,
            src_width=src_width,
            src_height=src_height,
            dst_width=dst_width,
            dst_height=dst_height,
        )
        if target is not None:
            targets.append(target)

    targets.sort(key=lambda item: (-item.confidence, item.click[1], item.click[0]))
    return targets


def post_multipart(
    *,
    base_url: str,
    image_path: str,
    prompt: str,
    max_pixels: int | None,
    raw: bool,
    timeout: float,
) -> dict[str, Any]:
    try:
        import httpx
    except ModuleNotFoundError:
        print(
            "error: httpx is not installed.\n"
            "hint: run `uv sync --group san5-vl-ground` from the workspace root first.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    url = f"{base_url.rstrip('/')}/v1/ground"
    data: dict[str, str] = {"prompt": prompt, "raw": "true" if raw else "false"}
    if max_pixels is not None:
        data["max_pixels"] = str(max_pixels)

    print(f"[san5] ground upload -> {url} ...", file=sys.stderr)
    with httpx.Client(timeout=timeout) as client:
        with Path(image_path).open("rb") as handle:
            response = client.post(
                url,
                data=data,
                files={"image": (Path(image_path).name, handle, "image/png")},
            )
    response.raise_for_status()
    body = response.json()
    if not isinstance(body, dict):
        raise ValueError(f"unexpected response type: {type(body).__name__}")
    return body


def post_ground_path(
    *,
    base_url: str,
    image_path: str,
    prompt: str,
    max_pixels: int | None,
    raw: bool,
    timeout: float,
) -> dict[str, Any]:
    try:
        import httpx
    except ModuleNotFoundError:
        print(
            "error: httpx is not installed.\n"
            "hint: run `uv sync --group san5-vl-ground` from the workspace root first.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    url = f"{base_url.rstrip('/')}/v1/ground/path"
    payload: dict[str, Any] = {
        "image_path": str(Path(image_path).expanduser()),
        "prompt": prompt,
        "raw": raw,
    }
    if max_pixels is not None:
        payload["max_pixels"] = max_pixels

    print(f"[san5] ground path -> {url} ...", file=sys.stderr)
    with httpx.Client(timeout=timeout) as client:
        response = client.post(url, json=payload)
    response.raise_for_status()
    body = response.json()
    if not isinstance(body, dict):
        raise ValueError(f"unexpected response type: {type(body).__name__}")
    return body


def call_ground_api(
    image_path: str,
    *,
    base_url: str,
    use_path: bool,
    prompt: str,
    max_pixels: int | None,
    raw: bool,
    timeout: float,
) -> tuple[list[OcrTarget], dict[str, Any]]:
    if use_path:
        data = post_ground_path(
            base_url=base_url,
            image_path=image_path,
            prompt=prompt,
            max_pixels=max_pixels,
            raw=raw,
            timeout=timeout,
        )
    else:
        data = post_multipart(
            base_url=base_url,
            image_path=image_path,
            prompt=prompt,
            max_pixels=max_pixels,
            raw=raw,
            timeout=timeout,
        )

    targets = targets_from_ground_response(data)
    return targets, data


def json_payload(
    targets: list[OcrTarget],
    *,
    image_path: str,
    base_url: str,
    ground_response: dict[str, Any],
    match: OcrTarget | None = None,
    query: str | None = None,
) -> dict:
    size = ground_response.get("image_size") if isinstance(ground_response.get("image_size"), dict) else {}
    return {
        "image": image_path,
        "backend": "san5-vl-ground",
        "base_url": base_url,
        "image_size": size,
        "detection_count": len(targets),
        "model_output": ground_response.get("model_output"),
        "targets": [asdict(target) for target in targets],
        "match_query": query,
        "recommended_click": asdict(match) if match is not None else None,
        "summary_line": summary_line(targets, image_path=image_path, match=match, query=query),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture (default) and ground a san5 screenshot via Qwen3-VL /v1/ground API.",
    )
    parser.add_argument(
        "image",
        nargs="?",
        default=None,
        help=f"PNG path; default after capture: {DEFAULT_IMAGE}",
    )
    parser.add_argument(
        "--no-capture",
        action="store_true",
        help="ground an existing PNG only (no scrot)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print structured JSON for automation",
    )
    parser.add_argument(
        "--match",
        help="pick the detection whose label best matches this text",
    )
    parser.add_argument(
        "--prompt",
        help="grounding prompt (default: SAN5_GROUND_PROMPT or built-in)",
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("SAN5_GROUND_BASE_URL", DEFAULT_BASE_URL),
        help=f"Grounding server root URL (default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--ground-path",
        action="store_true",
        help="use POST /v1/ground/path (image must exist on the server host)",
    )
    parser.add_argument(
        "--max-pixels",
        type=int,
        default=int(os.environ["SAN5_GROUND_MAX_PIXELS"])
        if os.environ.get("SAN5_GROUND_MAX_PIXELS")
        else None,
        help="optional max_pixels passed to the server",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        default=os.environ.get("SAN5_GROUND_RAW", "0") == "1",
        help="request raw model_output from server",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=float(os.environ.get("SAN5_GROUND_TIMEOUT", "180")),
        help="HTTP timeout seconds (default: 180)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="write the text or JSON output to a file",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    os.chdir(workspace_root())
    args = parse_args(argv)

    if args.no_capture:
        image_path = args.image or DEFAULT_IMAGE
    else:
        if args.image is not None:
            run_capture(Path(args.image))
            image_path = args.image
        else:
            print("[san5] capture -> ground...", file=sys.stderr)
            run_capture()
            image_path = DEFAULT_IMAGE

    if not Path(image_path).is_file():
        print(f"error: image not found: {image_path}", file=sys.stderr)
        print(
            "hint: run capture via san5_vl_ground.py (default) or skills/screenshot/scripts/san5_capture.py",
            file=sys.stderr,
        )
        return 1

    prompt = build_match_prompt(args.match, args.prompt)

    try:
        targets, ground_response = call_ground_api(
            image_path,
            base_url=args.base_url,
            use_path=args.ground_path,
            prompt=prompt,
            max_pixels=args.max_pixels,
            raw=args.raw,
            timeout=args.timeout,
        )
    except SystemExit:
        raise
    except Exception as exc:
        print(f"error: ground API failed: {exc}", file=sys.stderr)
        return 1

    match = find_match(targets, args.match)

    if args.json:
        content = json.dumps(
            json_payload(
                targets,
                image_path=image_path,
                base_url=args.base_url,
                ground_response=ground_response,
                match=match,
                query=args.match,
            ),
            ensure_ascii=False,
            indent=2,
        )
    else:
        size = ground_response.get("image_size", {})
        lines = [
            f"Ground found {len(targets)} target(s) in {image_path}.",
            f"server_image_size={size}",
        ]
        model_out = ground_response.get("model_output")
        if model_out and args.raw:
            lines.append(f"model_output: {model_out}")
        lines.append(describe_targets(targets, image_path=image_path, match=match, query=args.match))
        content = "\n".join(lines)

    if args.output:
        Path(args.output).write_text(
            content + ("\n" if not content.endswith("\n") else ""),
            encoding="utf-8",
        )
    else:
        print(content)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
