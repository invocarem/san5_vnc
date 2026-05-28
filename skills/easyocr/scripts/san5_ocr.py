#!/usr/bin/env python3
"""Capture (optional) and run EasyOCR on a san5 screenshot.

Examples:
  uv run --group easyocr python skills/easyocr/scripts/san5_ocr.py --json
  uv run --group easyocr python skills/easyocr/scripts/san5_ocr.py --json --match 確認
  uv run --group easyocr python skills/easyocr/scripts/san5_ocr.py --no-capture --json
  python3 skills/screenshot/scripts/san5_capture.py  # capture only

Environment:
  SAN5_SCREENSHOT          Default PNG after capture (default: screenshots/latest.png)
  SAN5_EASYOCR_LANGS       Comma-separated languages (default: ch_tra,en)
  SAN5_EASYOCR_MIN_CONFIDENCE
  SAN5_EASYOCR_GPU         Set to 1 to enable GPU
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

DEFAULT_IMAGE = os.environ.get("SAN5_SCREENSHOT", "screenshots/latest.png")
DEFAULT_WIDTH = 1024
DEFAULT_HEIGHT = 768
DEFAULT_LANGS = ("ch_tra", "en")
DEFAULT_MIN_CONFIDENCE = 0.5


@dataclass
class OcrTarget:
    label: str
    bbox: list[int]
    click: list[int]
    confidence: float


def workspace_root() -> Path:
    return Path(__file__).resolve().parents[3]


def run_capture(output: Path | None = None) -> None:
    root = workspace_root()
    os.chdir(root)
    scripts = root / "skills/screenshot/scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    import san5_capture

    argv: list[str] = [str(output)] if output is not None else []
    print("[san5] capture -> easyocr...", file=sys.stderr)
    rc = san5_capture.main(argv)
    if rc != 0:
        raise SystemExit(rc)


def screen_size() -> tuple[int, int]:
    width = int(os.environ.get("SAN5_SCREEN_WIDTH", str(DEFAULT_WIDTH)))
    height = int(os.environ.get("SAN5_SCREEN_HEIGHT", str(DEFAULT_HEIGHT)))
    return width, height


def parse_langs(raw: str | None) -> list[str]:
    if not raw:
        return list(DEFAULT_LANGS)
    langs = [part.strip() for part in raw.split(",") if part.strip()]
    return langs or list(DEFAULT_LANGS)


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", "", text).lower()


def clamp(value: int, lower: int, upper: int) -> int:
    return max(lower, min(upper, value))


def bbox_to_target(
    bbox: list[list[float]], text: str, confidence: float, *, width: int, height: int
) -> OcrTarget | None:
    label = text.strip()
    if not label:
        return None

    x_coords = [int(round(point[0])) for point in bbox]
    y_coords = [int(round(point[1])) for point in bbox]
    x1 = clamp(min(x_coords), 0, width - 1)
    x2 = clamp(max(x_coords), 0, width - 1)
    y1 = clamp(min(y_coords), 0, height - 1)
    y2 = clamp(max(y_coords), 0, height - 1)

    if x2 <= x1 or y2 <= y1:
        return None

    return OcrTarget(
        label=label,
        bbox=[x1, y1, x2, y2],
        click=[(x1 + x2) // 2, (y1 + y2) // 2],
        confidence=round(float(confidence), 4),
    )


def build_reader(langs: list[str], *, gpu: bool):
    try:
        import easyocr
    except ModuleNotFoundError:
        print(
            "error: easyocr is not installed.\n"
            "hint: run `uv sync --group easyocr` from the workspace root first.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    return easyocr.Reader(langs, gpu=gpu)


def read_targets(
    image_path: str,
    *,
    langs: list[str],
    min_confidence: float,
    gpu: bool,
) -> list[OcrTarget]:
    width, height = screen_size()
    reader = build_reader(langs, gpu=gpu)
    results = reader.readtext(image_path, detail=1, paragraph=False)

    targets: list[OcrTarget] = []
    for bbox, text, confidence in results:
        if float(confidence) < min_confidence:
            continue
        target = bbox_to_target(bbox, text, float(confidence), width=width, height=height)
        if target is not None:
            targets.append(target)

    targets.sort(key=lambda item: (-item.confidence, item.click[1], item.click[0]))
    return targets


def match_score(label: str, query: str) -> int | None:
    haystack = normalize_text(label)
    needle = normalize_text(query)
    if not haystack or not needle:
        return None
    if haystack == needle:
        return 300
    if needle in haystack:
        return 200 - abs(len(haystack) - len(needle))
    if haystack in needle:
        return 150 - abs(len(haystack) - len(needle))
    return None


def find_match(targets: list[OcrTarget], query: str | None) -> OcrTarget | None:
    if not query:
        return None

    best: tuple[int, float, OcrTarget] | None = None
    for target in targets:
        score = match_score(target.label, query)
        if score is None:
            continue
        candidate = (score, target.confidence, target)
        if best is None or candidate > best:
            best = candidate

    return None if best is None else best[2]


def summary_line(
    targets: list[OcrTarget],
    *,
    image_path: str,
    match: OcrTarget | None = None,
    query: str | None = None,
) -> str:
    parts = [f"ocr_targets={len(targets)}", f"image={Path(image_path).name}"]
    if match is not None:
        parts.append(
            f"match={query} -> {match.label} @ ({match.click[0]},{match.click[1]})"
        )
    elif targets:
        top = targets[0]
        parts.append(f"top={top.label} @ ({top.click[0]},{top.click[1]})")
    else:
        parts.append("no text targets above threshold")
    return " | ".join(parts)


def describe_targets(
    targets: list[OcrTarget],
    *,
    image_path: str,
    match: OcrTarget | None = None,
    query: str | None = None,
) -> str:
    lines = [f"OCR found {len(targets)} text target(s) in {image_path}."]
    for target in targets:
        x1, y1, x2, y2 = target.bbox
        cx, cy = target.click
        lines.append(
            f"- '{target.label}' bbox=({x1},{y1},{x2},{y2}) click=({cx},{cy}) confidence={target.confidence:.3f}"
        )

    if match is not None and query:
        lines.append(
            f"Best match for '{query}': '{match.label}' at ({match.click[0]},{match.click[1]})."
        )
    elif query:
        lines.append(f"No OCR target matched '{query}'.")

    return "\n".join(lines)


def json_payload(
    targets: list[OcrTarget],
    *,
    image_path: str,
    langs: list[str],
    min_confidence: float,
    match: OcrTarget | None = None,
    query: str | None = None,
) -> dict:
    return {
        "image": image_path,
        "languages": langs,
        "min_confidence": min_confidence,
        "targets": [asdict(target) for target in targets],
        "match_query": query,
        "recommended_click": asdict(match) if match is not None else None,
        "summary_line": summary_line(targets, image_path=image_path, match=match, query=query),
    }


def resolve_image_path(args: argparse.Namespace) -> str:
    if args.no_capture:
        return args.image or DEFAULT_IMAGE

    if args.image is not None:
        run_capture(Path(args.image))
        return args.image

    run_capture()
    return DEFAULT_IMAGE


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture (default) and analyze a san5 screenshot with EasyOCR.",
    )
    parser.add_argument(
        "image",
        nargs="?",
        default=None,
        help=f"PNG path for OCR; default after capture: {DEFAULT_IMAGE}",
    )
    parser.add_argument(
        "--no-capture",
        action="store_true",
        help="OCR an existing PNG only (no scrot)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print structured JSON for automation",
    )
    parser.add_argument(
        "--match",
        help="highlight the OCR result whose label best matches this text",
    )
    parser.add_argument(
        "--langs",
        default=os.environ.get("SAN5_EASYOCR_LANGS", ",".join(DEFAULT_LANGS)),
        help="comma-separated EasyOCR languages (default: ch_tra,en)",
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=float(os.environ.get("SAN5_EASYOCR_MIN_CONFIDENCE", str(DEFAULT_MIN_CONFIDENCE))),
        help=f"drop OCR results below this confidence (default: {DEFAULT_MIN_CONFIDENCE})",
    )
    parser.add_argument(
        "--gpu",
        action="store_true",
        default=os.environ.get("SAN5_EASYOCR_GPU", "0") == "1",
        help="enable GPU mode for EasyOCR",
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
    image_path = resolve_image_path(args)

    if not Path(image_path).is_file():
        print(f"error: image not found: {image_path}", file=sys.stderr)
        print(
            "hint: run capture via san5_ocr.py (default) or skills/screenshot/scripts/san5_capture.py",
            file=sys.stderr,
        )
        return 1

    langs = parse_langs(args.langs)
    targets = read_targets(
        image_path,
        langs=langs,
        min_confidence=args.min_confidence,
        gpu=args.gpu,
    )
    match = find_match(targets, args.match)

    if args.json:
        content = json.dumps(
            json_payload(
                targets,
                image_path=image_path,
                langs=langs,
                min_confidence=args.min_confidence,
                match=match,
                query=args.match,
            ),
            ensure_ascii=False,
            indent=2,
        )
    else:
        content = describe_targets(
            targets,
            image_path=image_path,
            match=match,
            query=args.match,
        )

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
