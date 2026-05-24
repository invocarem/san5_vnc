#!/usr/bin/env python3
"""Send a san5 screenshot to ModelBest MiniCPM-V and print vision target analysis.

Examples:
  export MODELBEST_API_KEY=sk-...
  python3 skills/minicpm-vision/scripts/analyze_screenshot.py --capture
  python3 skills/minicpm-vision/scripts/analyze_screenshot.py san5_screenshot.png
  python3 skills/minicpm-vision/scripts/analyze_screenshot.py --capture --json
  python3 skills/minicpm-vision/scripts/analyze_screenshot.py -o analysis.md
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path

DEFAULT_API_BASE = "https://api.modelbest.cn/v1"
DEFAULT_MODEL = "MiniCPM-V-4.6-Instruct"
DEFAULT_IMAGE = "san5_screenshot.png"
DEFAULT_WIDTH = 1024
DEFAULT_HEIGHT = 768
MAX_CALIBRATION_OFFSET = int(os.environ.get("SAN5_MAX_CALIBRATION_OFFSET", "80"))

SAN5_VISION_PROMPT = """You are analyzing a screenshot of Romance of the Three Kingdoms V (三国志V) running in DOSBox.

Image size is exactly 1024×768 pixels. Origin (0,0) is the top-left corner.

Identify clickable UI elements (buttons, menu items, dialog choices). For each target:
- bbox: four INTEGERS (x1,y1,x2,y2) in pixel space — top-left and bottom-right corners
- click: two INTEGERS (cx,cy) = center of the bbox

Also locate the **game cursor** — the white hand/arrow sprite drawn INSIDE the game (not an OS pointer).
Report the **tip/hotspot** pixel of that sprite. If no game cursor is visible, say visible: no.

CRITICAL: use pixel integers only (0–1023 for x, 0–767 for y). Do NOT use fractions, percentages, or normalized 0–1 values.

Layout rules (do not guess center — use visible button positions):
- **main_menu**: one centered vertical menu (~x 380–640, y 270–490). Six items (開始新遊戲, 載入遊戲進度, …). Background birds are NOT buttons.
- **map** (in-game): LEFT side is terrain only — no buttons there. ALL controls are in the RIGHT panel (x ≥ 540): red menu bar + large green buttons (外交, 計謀, 軍事, 人事, 內政, 特殊, 休息, …).
- **dialog**: modal box near screen center; 確認/取消 inside the box.

Do NOT list the whole map, background, or full window as a target. Do NOT put map-screen buttons at x < 500.

Example row (follow this format exactly; integer pixels only):
| label | x1,y1,x2,y2 | cx,cy |

Known verified anchors (e.g. CD 確認): see skills/san5-ui/SKILL.md.

Respond ONLY in this markdown template (fill every section; use "none" if empty):

## Screen
- type: dialog | main_menu | map | battle | other
- summary: one line

## Message
- text: (dialog or status text, or none)

## Cursor
- visible: yes | no
- tip: (cx, cy) or none

## Targets
| label | bbox (x1,y1,x2,y2) | click (cx,cy) |
|-------|---------------------|---------------|
| (one row per button, integer coords only) |

## Next action
- click: (label of the best next button, or none)
"""

SAN5_CURSOR_RETRY_PROMPT = """Screenshot of Romance of the Three Kingdoms V (三国志V). Image is 1024×768 pixels, origin top-left.

Find the white hand/arrow cursor sprite drawn INSIDE the game (not an OS pointer).
Report ONLY JSON — no markdown:
{"visible": true, "tip": [x, y]}
or if no game cursor is visible:
{"visible": false}

x and y must be integer pixel coordinates of the cursor tip/hotspot.
"""


def parse_cursor_json(content: str, *, w: int, h: int) -> list[int] | None:
    text = content.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    if not data.get("visible"):
        return None
    tip = data.get("tip")
    if isinstance(tip, list) and len(tip) >= 2:
        return [_to_pixel(float(tip[0]), w), _to_pixel(float(tip[1]), h)]
    return None


SAN5_COORDS_RETRY_PROMPT = """This screenshot is Romance of the Three Kingdoms V (三国志V) at 1024×768 pixels.

List every clickable button or menu item. Return ONLY a JSON array — no markdown, no explanation.

Each element:
{"label": "button text", "bbox": [x1, y1, x2, y2], "click": [cx, cy]}

Rules:
- All numbers must be integers in pixel space (x: 0–1023, y: 0–767)
- click must be the center of bbox
- Do not use fractions or percentages
- On the in-game map screen, only buttons in the RIGHT UI panel (x ≥ 540); ignore terrain on the left
"""

SAN5_MAP_PANEL_RETRY_PROMPT = """Romance of the Three Kingdoms V (三国志V) in-game map screen. Image: 1024×768 px, origin top-left.

The LEFT side (~x 0–520) is map terrain — NOT clickable.

List ONLY buttons in the RIGHT command panel (x ≥ 540): red menu bar (移動, 戰爭, 君主, …) and large green buttons (外交, 計謀, 軍事, 人事, 內政, 特殊, 休息, …).

Return ONLY a JSON array. Each element:
{"label": "exact Chinese label on button", "bbox": [x1, y1, x2, y2], "click": [cx, cy]}
Integer pixels only (x: 540–1023). Do not use 0–1000 scale.
"""

SAN5_MAIN_MENU_RETRY_PROMPT = """Romance of the Three Kingdoms V (三国志V) main title menu. Image: 1024×768 px.

A single centered vertical menu (~x 380–640, y 270–490) with six items:
開始新遊戲, 載入遊戲進度, 登錄武將資料, 武將單挑, 登錄寶物資料, 轉換儲存資料.

Return ONLY a JSON array of those buttons with integer pixel bboxes and click centers. Ignore background pattern.
"""

# Screen-type layout validation (1024×768). Used to filter hallucinated coords.
SCREEN_PROFILES: dict[str, dict] = {
    "main_menu": {
        "aliases": frozenset({"main_menu", "menu", "title", "title_screen"}),
        "click_x": (360, 660),
        "click_y": (260, 520),
        "retry_prompt": SAN5_MAIN_MENU_RETRY_PROMPT,
    },
    "map": {
        "aliases": frozenset({"map", "strategy", "tactical", "in_game", "ingame"}),
        "click_x": (540, 1023),
        "click_y": (40, 700),
        "retry_prompt": SAN5_MAP_PANEL_RETRY_PROMPT,
    },
    "dialog": {
        "aliases": frozenset({"dialog", "modal", "confirm"}),
        "click_x": (180, 844),
        "click_y": (280, 560),
        "retry_prompt": None,
    },
}

IGNORE_TARGET_LABELS = frozenset(
    {
        "label",
        "cursor",
        "游標",
        "游戏光标",
        "遊戲光標",
        "地图",
        "地圖",
        "map",
        "主菜单",
        "主菜單",
        "主界面",
        "主畫面",
        "背景",
        "background",
        "screen",
        "window",
    }
)

MAX_BBOX_AREA_FRAC = 0.35


@dataclass
class VisionTarget:
    label: str
    bbox: list[int]
    click: list[int]
    calibrated_click: list[int] | None = None


@dataclass
class CursorCalibration:
    debug: list[int] | None = None
    vision: list[int] | None = None
    offset: list[int] | None = None
    active: bool = False
    reason: str = ""


@dataclass
class VisionResult:
    screen_type: str = "other"
    summary: str = ""
    message: str = ""
    next_action: str = ""
    targets: list[VisionTarget] = field(default_factory=list)
    raw_markdown: str = ""
    coords_source: str = "primary"
    cursor: CursorCalibration = field(default_factory=CursorCalibration)
    warnings: list[str] = field(default_factory=list)
    coord_confidence: str = "unknown"


def log(msg: str, *, quiet: bool = False) -> None:
    if quiet:
        return
    elapsed = time.monotonic() - _START_TIME
    print(f"[san5-vision {elapsed:5.1f}s] {msg}", file=sys.stderr, flush=True)


_START_TIME = time.monotonic()


def screen_size() -> tuple[int, int]:
    w = int(os.environ.get("SAN5_SCREEN_WIDTH", str(DEFAULT_WIDTH)))
    h = int(os.environ.get("SAN5_SCREEN_HEIGHT", str(DEFAULT_HEIGHT)))
    return w, h


def dosbox_mouse_script() -> Path:
    return Path(__file__).resolve().parents[2] / "dosbox-mouse/scripts/dosbox_mouse.py"


def get_debug_cursor(*, quiet: bool = False) -> list[int] | None:
    """Run dosbox_mouse -a debug and parse inside-window position."""
    script = dosbox_mouse_script()
    if not script.is_file():
        log(f"warning: dosbox_mouse not found at {script}", quiet=quiet)
        return None
    cmd = ["python3", str(script), "-a", "debug"]
    log(f"debug cursor: {' '.join(cmd)}", quiet=quiet)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        log(f"warning: debug failed: {proc.stderr.strip() or proc.stdout.strip()}", quiet=quiet)
        return None
    m = re.search(r"inside window \((\d+),\s*(\d+)\)", proc.stdout)
    if not m:
        log(f"warning: could not parse debug output", quiet=quiet)
        return None
    pos = [int(m.group(1)), int(m.group(2))]
    log(f"debug cursor at ({pos[0]},{pos[1]})", quiet=quiet)
    return pos


def wake_cursor_at(x: int, y: int, *, quiet: bool = False) -> None:
    """Sync X11 pointer to DOSBox so the game cursor appears at capture position."""
    script = dosbox_mouse_script()
    if not script.is_file():
        return
    cmd = ["python3", str(script), "-a", "move", "-p", str(x), str(y), "--sync"]
    log(f"wake game cursor: {' '.join(cmd)}", quiet=quiet)
    subprocess.run(cmd, capture_output=True, text=True)
    time.sleep(float(os.environ.get("SAN5_SETTLE_SEC", "0.45")))


def build_vision_prompt() -> str:
    """Primary vision prompt. Do not inject debug cursor — it biases the model."""
    return SAN5_VISION_PROMPT


def normalize_screen_type(raw: str) -> str:
    t = raw.lower().strip()
    for key, profile in SCREEN_PROFILES.items():
        if t == key or t in profile["aliases"]:
            return key
    return t


def screen_profile(screen_type: str) -> dict | None:
    return SCREEN_PROFILES.get(normalize_screen_type(screen_type))


def click_in_profile(x: int, y: int, profile: dict) -> bool:
    x1, x2 = profile["click_x"]
    y1, y2 = profile["click_y"]
    return x1 <= x <= x2 and y1 <= y <= y2


def bbox_area_frac(bbox: list[int], w: int, h: int) -> float:
    x1, y1, x2, y2 = bbox
    return (x2 - x1) * (y2 - y1) / (w * h)


def _parse_paren_points(text: str) -> list[tuple[int, int]]:
    points: list[tuple[int, int]] = []
    for m in re.finditer(r"\(\s*(\d+)\s*[,，]\s*(\d+)\s*\)", text):
        points.append((int(m.group(1)), int(m.group(2))))
    return points


def _parse_kv_bbox_click(text: str, w: int, h: int) -> tuple[list[int], list[int]] | None:
    """Parse x1:540,y1:270,x2:640,y2:490 and cx:590,cy:337 style fields."""
    fields: dict[str, int] = {}
    for m in re.finditer(r"\b(x[12]|y[12]|cx|cy)\s*[:=]\s*(\d+)", text, re.I):
        fields[m.group(1).lower()] = int(m.group(2))
    need_bbox = {"x1", "y1", "x2", "y2"}
    if not need_bbox.issubset(fields):
        return None
    bbox = _bbox_from_nums(
        [fields["x1"], fields["y1"], fields["x2"], fields["y2"]], w, h
    )
    if bbox is None or not _valid_bbox(bbox, w, h):
        return None
    if "cx" in fields and "cy" in fields:
        click = [_to_pixel(fields["cx"], w), _to_pixel(fields["cy"], h)]
    else:
        click = _click_from_bbox(bbox)
    return bbox, click


def _rescale_point(x: int, y: int, w: int, h: int) -> list[int]:
    return [_clamp(int(round(x * w / 1000)), 0, w - 1), _clamp(int(round(y * h / 1000)), 0, h - 1)]


def _looks_milligrid(targets: list[VisionTarget]) -> bool:
    if not targets:
        return False
    return max(t.click[0] for t in targets) <= 1000 and max(t.click[1] for t in targets) <= 1000


def _rescale_targets_milligrid(targets: list[VisionTarget], w: int, h: int) -> None:
    for t in targets:
        t.click = _rescale_point(t.click[0], t.click[1], w, h)
        if len(t.bbox) >= 4:
            bx1, by1 = _rescale_point(t.bbox[0], t.bbox[1], w, h)
            bx2, by2 = _rescale_point(t.bbox[2], t.bbox[3], w, h)
            if bx2 > bx1 and by2 > by1:
                t.bbox = [bx1, by1, bx2, by2]


def sanitize_targets(result: VisionResult, *, w: int, h: int, quiet: bool = False) -> list[VisionTarget]:
    """Drop junk rows; optionally rescale 0–1000 coords; filter by screen layout."""
    profile = screen_profile(result.screen_type)
    kept: list[VisionTarget] = []

    if _looks_milligrid(result.targets):
        _rescale_targets_milligrid(result.targets, w, h)
        result.warnings.append("rescaled coordinates from 0–1000 grid to 1024×768 pixels")

    for t in result.targets:
        label_key = t.label.strip().lower()
        if label_key in IGNORE_TARGET_LABELS or "cursor" in label_key:
            continue
        if bbox_area_frac(t.bbox, w, h) > MAX_BBOX_AREA_FRAC:
            continue
        if profile and not click_in_profile(t.click[0], t.click[1], profile):
            continue
        kept.append(t)

    dropped = len(result.targets) - len(kept)
    if dropped:
        msg = f"filtered {dropped} target(s) outside {result.screen_type} layout or junk labels"
        result.warnings.append(msg)
        log(msg, quiet=quiet)
    result.targets = kept
    return kept


def valid_targets_for_screen(result: VisionResult) -> list[VisionTarget]:
    profile = screen_profile(result.screen_type)
    if not profile:
        return result.targets
    return [t for t in result.targets if click_in_profile(t.click[0], t.click[1], profile)]


def needs_regional_retry(result: VisionResult) -> bool:
    profile = screen_profile(result.screen_type)
    if not profile or not profile.get("retry_prompt"):
        return False
    valid = valid_targets_for_screen(result)
    return len(valid) == 0


def assess_coord_confidence(result: VisionResult) -> str:
    profile = screen_profile(result.screen_type)
    if not result.targets:
        return "none"
    valid = valid_targets_for_screen(result) if profile else result.targets
    if not valid:
        return "low"
    if len(valid) == len(result.targets):
        return "high"
    return "medium"


def regional_retry_prompt(result: VisionResult) -> str | None:
    profile = screen_profile(result.screen_type)
    if profile:
        return profile.get("retry_prompt")
    return None


def image_data_url(path: str) -> str:
    mime, _ = mimetypes.guess_type(path)
    if not mime or not mime.startswith("image/"):
        mime = "image/png"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def capture_screenshot(path: str, *, quiet: bool = False) -> None:
    display = os.environ.get("SAN5_DISPLAY", ":99")
    w, h = screen_size()
    region = f"0,0,{w},{h}"
    cmd = ["scrot", "-D", display, "-a", region, path]
    log(f"capture: {' '.join(cmd)}", quiet=quiet)
    subprocess.run(cmd, check=True)
    log(f"capture done → {path}", quiet=quiet)


def chat_completion(
    *,
    api_base: str,
    api_key: str,
    model: str,
    prompt: str,
    image_path: str,
    timeout: float,
    quiet: bool = False,
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
    log(f"API request → {model} (timeout {timeout:.0f}s, image {image_path})", quiet=quiet)
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    t0 = time.monotonic()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    log(f"API response ({time.monotonic() - t0:.1f}s)", quiet=quiet)
    return data


def extract_content(data: dict) -> str:
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise ValueError(f"unexpected API response: {data!r}") from e


def _clamp(v: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, v))


def _to_pixel(value: float, axis_max: int) -> int:
    """Convert a coordinate that may be normalized (0–1) or already in pixels."""
    if 0 < value <= 1.0:
        return _clamp(int(round(value * axis_max)), 0, axis_max - 1)
    return _clamp(int(round(value)), 0, axis_max - 1)


def _parse_int_list(text: str) -> list[int] | None:
    nums = [float(x) for x in re.findall(r"-?\d+\.?\d*", text)]
    return None if not nums else nums


def _parse_table_row(line: str, w: int, h: int) -> VisionTarget | None:
    stripped = line.strip()
    if not stripped.startswith("|"):
        return None
    if re.match(r"^\|\s*[-label]+\s*\|", stripped, re.I):
        return None

    cells = [c.strip() for c in stripped.strip("|").split("|")]
    if len(cells) < 2:
        return None

    label = cells[0]
    if not label or label.lower() in {"label", "(rows for each button)", "(one row per button, integer coords only)"}:
        return None
    if label.strip().lower() in IGNORE_TARGET_LABELS:
        return None

    rest = " ".join(cells[1:])
    kv = _parse_kv_bbox_click(rest, w, h)
    if kv:
        bbox, click = kv
        return VisionTarget(label=label, bbox=bbox, click=click)

    points = _parse_paren_points(rest)

    # Format: (x1,y1), (x2,y2) | (cx,cy)  OR  (x1,y1,x2,y2) style via flat nums
    if len(points) >= 3:
        (x1, y1), (x2, y2), (cx, cy) = points[0], points[1], points[-1]
        bbox = _bbox_from_nums([x1, y1, x2, y2], w, h)
        if bbox is None or not _valid_bbox(bbox, w, h):
            return None
        click = [_to_pixel(cx, w), _to_pixel(cy, h)]
        return VisionTarget(label=label, bbox=bbox, click=click)

    if len(points) == 2:
        cx, cy = _to_pixel(points[0][0], w), _to_pixel(points[0][1], h)
        cx2, cy2 = _to_pixel(points[1][0], w), _to_pixel(points[1][1], h)
        if abs(cx2 - cx) > 30 or abs(cy2 - cy) > 30:
            bbox = _bbox_from_nums([points[0][0], points[0][1], points[1][0], points[1][1]], w, h)
            if bbox and _valid_bbox(bbox, w, h):
                click = _click_from_bbox(bbox)
                return VisionTarget(label=label, bbox=bbox, click=click)
        cx, cy = cx2, cy2

    if len(points) == 1:
        cx, cy = _to_pixel(points[0][0], w), _to_pixel(points[0][1], h)
        bbox = [
            _clamp(cx - 20, 0, w - 1),
            _clamp(cy - 10, 0, h - 1),
            _clamp(cx + 20, 0, w - 1),
            _clamp(cy + 10, 0, h - 1),
        ]
        return VisionTarget(label=label, bbox=bbox, click=[cx, cy])

    nums = _parse_int_list(rest)
    if nums is None:
        return None

    if len(nums) == 2:
        cx, cy = _to_pixel(nums[0], w), _to_pixel(nums[1], h)
        bbox = [
            _clamp(cx - 20, 0, w - 1),
            _clamp(cy - 10, 0, h - 1),
            _clamp(cx + 20, 0, w - 1),
            _clamp(cy + 10, 0, h - 1),
        ]
        return VisionTarget(label=label, bbox=bbox, click=[cx, cy])

    bbox = _bbox_from_nums(nums[:4], w, h)
    if bbox is None or not _valid_bbox(bbox, w, h):
        return None

    click_nums = nums[4:6] if len(nums) >= 6 else []
    click = _click_from_nums(click_nums, bbox, w, h) if click_nums else _click_from_bbox(bbox)
    return VisionTarget(label=label, bbox=bbox, click=click)


def _parse_markdown_rows(content: str, w: int, h: int) -> list[VisionTarget]:
    targets: list[VisionTarget] = []
    seen: set[str] = set()
    for line in content.splitlines():
        t = _parse_table_row(line, w, h)
        if t and t.label not in seen:
            targets.append(t)
            seen.add(t.label)
    return targets


def _bbox_from_nums(nums: list[float], w: int, h: int) -> list[int] | None:
    if len(nums) < 4:
        return None
    x1 = _to_pixel(nums[0], w)
    y1 = _to_pixel(nums[1], h)
    x2 = _to_pixel(nums[2], w)
    y2 = _to_pixel(nums[3], h)
    if x2 <= x1 or y2 <= y1:
        return None
    return [x1, y1, x2, y2]


def _click_from_bbox(bbox: list[int]) -> list[int]:
    return [(bbox[0] + bbox[2]) // 2, (bbox[1] + bbox[3]) // 2]


def _click_from_nums(nums: list[float], bbox: list[int], w: int, h: int) -> list[int]:
    if len(nums) >= 2:
        return [_to_pixel(nums[0], w), _to_pixel(nums[1], h)]
    return _click_from_bbox(bbox)


def _valid_bbox(bbox: list[int], w: int, h: int) -> bool:
    x1, y1, x2, y2 = bbox
    return 0 <= x1 < x2 <= w and 0 <= y1 < y2 <= h


def parse_markdown_analysis(content: str, *, w: int, h: int) -> VisionResult:
    result = VisionResult(raw_markdown=content)

    m = re.search(r"type:\s*(\w+)", content, re.I)
    if m:
        result.screen_type = normalize_screen_type(m.group(1))

    m = re.search(r"summary:\s*(.+)", content, re.I)
    if m:
        result.summary = m.group(1).strip()

    m = re.search(r"text:\s*(.+)", content, re.I)
    if m:
        result.message = m.group(1).strip()

    m = re.search(r"click:\s*(.+)", content, re.I)
    if m:
        result.next_action = m.group(1).strip()

    in_targets = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("## targets"):
            in_targets = True
            continue
        if in_targets and stripped.startswith("## "):
            break
        if in_targets and stripped.startswith("|"):
            t = _parse_table_row(stripped, w, h)
            if t:
                result.targets.append(t)

    # Model often skips ## Targets header — scan all pipe rows
    if not result.targets:
        result.targets = _parse_markdown_rows(content, w, h)

    if result.targets and (not result.next_action or result.next_action.lower() == "none"):
        result.next_action = result.targets[0].label

    result.cursor.vision = parse_vision_cursor(content, w=w, h=h)

    return result


def parse_vision_cursor(content: str, *, w: int, h: int) -> list[int] | None:
    """Extract game cursor tip from ## Cursor section."""
    section = ""
    in_cursor = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("## cursor"):
            in_cursor = True
            continue
        if in_cursor and stripped.startswith("## "):
            break
        if in_cursor:
            section += stripped + "\n"

    if re.search(r"visible:\s*no\b", section, re.I):
        return None

    for pattern in (
        r"tip:\s*\(?\s*(\d+)\s*,\s*(\d+)\s*\)?",
        r"position:\s*\(?\s*(\d+)\s*,\s*(\d+)\s*\)?",
        r"cursor[^0-9]*(\d+)\s*,\s*(\d+)",
    ):
        m = re.search(pattern, section, re.I)
        if m:
            return [_to_pixel(float(m.group(1)), w), _to_pixel(float(m.group(2)), h)]

    # Fallback: scan whole doc for cursor tip line
    m = re.search(r"tip:\s*\(?\s*(\d+)\s*,\s*(\d+)\s*\)?", content, re.I)
    if m:
        return [int(m.group(1)), int(m.group(2))]
    return None


def apply_calibration(result: VisionResult) -> None:
    """Compare debug vs vision cursor; shift target clicks only when anchors agree."""
    cal = result.cursor
    if cal.debug is None:
        cal.reason = "no debug cursor (dosbox_mouse -a debug failed)"
        return
    if cal.vision is None:
        cal.reason = "vision did not report game cursor tip"
        return

    dx = cal.debug[0] - cal.vision[0]
    dy = cal.debug[1] - cal.vision[1]
    dist = (dx * dx + dy * dy) ** 0.5
    cal.offset = [dx, dy]

    if dist < 2:
        cal.active = False
        cal.reason = f"offset negligible ({dx:+d},{dy:+d})"
        for t in result.targets:
            t.calibrated_click = t.click.copy()
        return

    if dist > MAX_CALIBRATION_OFFSET:
        cal.active = False
        cal.reason = (
            f"offset too large ({dx:+d},{dy:+d}, {dist:.0f}px) — "
            "screenshot cursor likely out of sync; not shifting button coords"
        )
        result.warnings.append(cal.reason)
        return

    # Do not shift buttons when vision cursor disagrees with layout (e.g. center-biased tip)
    profile = screen_profile(result.screen_type)
    if profile and not click_in_profile(cal.vision[0], cal.vision[1], profile):
        cal.active = False
        cal.reason = (
            f"vision cursor ({cal.vision[0]},{cal.vision[1]}) outside {result.screen_type} "
            f"layout — skipping button calibration"
        )
        result.warnings.append(cal.reason)
        return

    cal.active = True
    cal.reason = f"applied offset ({dx:+d},{dy:+d}) from cursor anchor"
    w, h = screen_size()
    for t in result.targets:
        cx = _clamp(t.click[0] + dx, 0, w - 1)
        cy = _clamp(t.click[1] + dy, 0, h - 1)
        t.calibrated_click = [cx, cy]
    log(f"calibration: debug={cal.debug} vision={cal.vision} → offset=({dx:+d},{dy:+d})", quiet=False)


def parse_json_targets(content: str, *, w: int, h: int) -> list[VisionTarget]:
    text = content.strip()
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        return []

    try:
        items = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return []

    targets: list[VisionTarget] = []
    if not isinstance(items, list):
        return targets

    for item in items:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label", "")).strip()
        bbox_raw = item.get("bbox")
        click_raw = item.get("click")
        if not label or not isinstance(bbox_raw, list) or len(bbox_raw) < 4:
            continue
        bbox = _bbox_from_nums([float(x) for x in bbox_raw[:4]], w, h)
        if bbox is None or not _valid_bbox(bbox, w, h):
            continue
        if isinstance(click_raw, list) and len(click_raw) >= 2:
            click = _click_from_nums([float(x) for x in click_raw[:2]], bbox, w, h)
        else:
            click = _click_from_bbox(bbox)
        targets.append(VisionTarget(label=label, bbox=bbox, click=click))
    return targets


def effective_click(target: VisionTarget, result: VisionResult) -> list[int]:
    if target.calibrated_click and result.cursor.active:
        return target.calibrated_click
    return target.click


def pick_next_target(result: VisionResult) -> VisionTarget | None:
    if not result.targets:
        return None
    want = result.next_action.strip()
    if want and want.lower() != "none":
        for t in result.targets:
            if want in t.label or t.label in want:
                return t
    return result.targets[0]


def format_summary(result: VisionResult) -> str:
    parts = [f"screen={result.screen_type}"]
    if result.coord_confidence not in ("unknown", "high"):
        parts.append(f"coord_confidence={result.coord_confidence}")
    if result.summary:
        parts.append(result.summary)
    if result.cursor.debug:
        parts.append(f"debug_cursor=({result.cursor.debug[0]},{result.cursor.debug[1]})")
    if result.cursor.active and result.cursor.offset:
        ox, oy = result.cursor.offset
        parts.append(f"calibrated ({ox:+d},{oy:+d})")
    elif result.cursor.reason and result.cursor.debug:
        parts.append(f"calibration skipped ({result.cursor.reason})")
    nxt = pick_next_target(result)
    if nxt:
        cx, cy = effective_click(nxt, result)
        raw = nxt.click
        if result.cursor.active and nxt.calibrated_click and nxt.calibrated_click != raw:
            parts.append(f"next={nxt.label} @ ({cx},{cy}) [raw ({raw[0]},{raw[1]})]")
        else:
            parts.append(f"next={nxt.label} @ ({cx},{cy})")
    elif result.next_action and result.next_action.lower() != "none":
        parts.append(f"next={result.next_action} (no coords)")
    else:
        parts.append("no clickable targets")
    return " | ".join(parts)


def retry_cursor_vision(
    *,
    image_path: str,
    api_base: str,
    api_key: str,
    model: str,
    timeout: float,
    quiet: bool = False,
) -> list[int] | None:
    log("cursor retry: asking model for game cursor tip (JSON)", quiet=quiet)
    data = chat_completion(
        api_base=api_base,
        api_key=api_key,
        model=model,
        prompt=SAN5_CURSOR_RETRY_PROMPT,
        image_path=image_path,
        timeout=timeout,
        quiet=quiet,
    )
    content = extract_content(data)
    w, h = screen_size()
    return parse_cursor_json(content, w=w, h=h)


def finalize_calibration(result: VisionResult, *, quiet: bool = False) -> None:
    if result.cursor.debug is None:
        return
    apply_calibration(result)
    if not result.cursor.active and result.cursor.reason:
        log(f"calibration: {result.cursor.reason}", quiet=quiet)


def _fetch_json_targets(
    *,
    prompt: str,
    image_path: str,
    api_base: str,
    api_key: str,
    model: str,
    timeout: float,
    quiet: bool,
    source_label: str,
) -> list[VisionTarget]:
    data = chat_completion(
        api_base=api_base,
        api_key=api_key,
        model=model,
        prompt=prompt,
        image_path=image_path,
        timeout=timeout,
        quiet=quiet,
    )
    w, h = screen_size()
    return parse_json_targets(extract_content(data), w=w, h=h)


def analyze_image(
    *,
    image_path: str,
    api_base: str,
    api_key: str,
    model: str,
    timeout: float,
    quiet: bool = False,
    retry_coords: bool = True,
    known_cursor: list[int] | None = None,
    calibrate: bool = False,
) -> VisionResult:
    w, h = screen_size()

    log("step 1/4: calling vision model for screen description", quiet=quiet)
    data = chat_completion(
        api_base=api_base,
        api_key=api_key,
        model=model,
        prompt=build_vision_prompt(),
        image_path=image_path,
        timeout=timeout,
        quiet=quiet,
    )
    content = extract_content(data)
    result = parse_markdown_analysis(content, w=w, h=h)
    result.raw_markdown = content
    result.coords_source = "primary"
    sanitize_targets(result, w=w, h=h, quiet=quiet)

    if calibrate and known_cursor:
        result.cursor.debug = known_cursor

    if retry_coords and needs_regional_retry(result):
        regional = regional_retry_prompt(result)
        if regional:
            log(
                f"step 2/4: coords outside {result.screen_type} layout — regional JSON retry",
                quiet=quiet,
            )
            targets = _fetch_json_targets(
                prompt=regional,
                image_path=image_path,
                api_base=api_base,
                api_key=api_key,
                model=model,
                timeout=timeout,
                quiet=quiet,
                source_label="regional",
            )
            if targets:
                result.targets = targets
                result.coords_source = "retry_regional"
                sanitize_targets(result, w=w, h=h, quiet=quiet)
                if not result.next_action or result.next_action.lower() == "none":
                    result.next_action = targets[0].label
                log(f"parsed {len(targets)} target(s) from regional retry", quiet=quiet)

    if result.targets and result.coords_source == "primary":
        log(f"parsed {len(result.targets)} target(s) from markdown", quiet=quiet)

    if not result.targets and retry_coords:
        log("step 3/4: no usable targets — generic JSON retry", quiet=quiet)
        targets = _fetch_json_targets(
            prompt=SAN5_COORDS_RETRY_PROMPT,
            image_path=image_path,
            api_base=api_base,
            api_key=api_key,
            model=model,
            timeout=timeout,
            quiet=quiet,
            source_label="json",
        )
        if targets:
            result.targets = targets
            result.coords_source = "retry_json"
            sanitize_targets(result, w=w, h=h, quiet=quiet)
            if not result.next_action or result.next_action.lower() == "none":
                result.next_action = targets[0].label
            log(f"parsed {len(targets)} target(s) from JSON retry", quiet=quiet)
        else:
            log("warning: retry still returned no usable pixel coordinates", quiet=quiet)

    if calibrate and known_cursor:
        result.cursor.debug = known_cursor
        if result.cursor.vision is None:
            vision = retry_cursor_vision(
                image_path=image_path,
                api_base=api_base,
                api_key=api_key,
                model=model,
                timeout=timeout,
                quiet=quiet,
            )
            if vision:
                result.cursor.vision = vision
        finalize_calibration(result, quiet=quiet)
        if result.cursor.debug and result.cursor.vision:
            dx = abs(result.cursor.debug[0] - result.cursor.vision[0])
            dy = abs(result.cursor.debug[1] - result.cursor.vision[1])
            if dx + dy > 40:
                result.warnings.append(
                    f"debug cursor {result.cursor.debug} vs vision tip {result.cursor.vision} "
                    f"— capture may be stale; prefer debug for cursor, layout-filtered coords for buttons"
                )

    result.coord_confidence = assess_coord_confidence(result)
    if result.coord_confidence == "low":
        result.warnings.append(
            "no targets passed layout validation — use skills/san5-ui known coords or re-capture"
        )

    return result


def target_to_dict(target: VisionTarget, result: VisionResult) -> dict:
    d = asdict(target)
    d["use_click"] = effective_click(target, result)
    return d


def result_to_json(result: VisionResult) -> dict:
    nxt = pick_next_target(result)
    rec = None
    if nxt:
        rec = target_to_dict(nxt, result)
        rec["click"] = nxt.click
        rec["calibrated_click"] = nxt.calibrated_click
        rec["use_click"] = effective_click(nxt, result)
    return {
        "screen_type": result.screen_type,
        "summary": result.summary,
        "message": result.message,
        "next_action": result.next_action,
        "coords_source": result.coords_source,
        "coord_confidence": result.coord_confidence,
        "warnings": result.warnings,
        "cursor": asdict(result.cursor),
        "debug_cursor": result.cursor.debug,
        "targets": [target_to_dict(t, result) for t in result.targets],
        "recommended_click": rec,
        "summary_line": format_summary(result),
        "raw_markdown": result.raw_markdown,
    }


def main(argv: list[str] | None = None) -> int:
    global _START_TIME
    _START_TIME = time.monotonic()

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
        default=float(os.environ.get("MODELBEST_TIMEOUT", "120")),
    )
    p.add_argument("--raw", action="store_true", help="print full JSON API response")
    p.add_argument(
        "--json",
        action="store_true",
        help="print structured JSON with parsed targets and recommended_click",
    )
    p.add_argument(
        "--no-retry",
        action="store_true",
        help="do not retry with JSON prompt when markdown lacks pixel coords",
    )
    p.add_argument(
        "--quiet",
        action="store_true",
        help="suppress [san5-vision] progress lines on stderr",
    )
    p.add_argument(
        "--calibrate",
        action="store_true",
        help="run dosbox_mouse debug before capture; use game cursor to fix coords",
    )
    p.add_argument(
        "--no-calibrate",
        action="store_true",
        help="skip cursor calibration even with --capture",
    )
    args = p.parse_args(argv)

    api_key = os.environ.get("MODELBEST_API_KEY")
    if not api_key:
        print(
            "error: set MODELBEST_API_KEY (see skills/minicpm-vision/SKILL.md)",
            file=sys.stderr,
        )
        return 1

    image_path = args.image
    calibrate = args.calibrate or (args.capture and not args.no_calibrate)
    known_cursor: list[int] | None = None

    if calibrate:
        log("step 0/3: reading cursor from dosbox_mouse debug", quiet=args.quiet)
        known_cursor = get_debug_cursor(quiet=args.quiet)
        if known_cursor:
            wake_cursor_at(known_cursor[0], known_cursor[1], quiet=args.quiet)

    if args.capture:
        step = "1/4" if calibrate else "0/3"
        log(f"step {step}: capturing screenshot", quiet=args.quiet)
        capture_screenshot(image_path, quiet=args.quiet)
    elif not os.path.isfile(image_path):
        print(f"error: image not found: {image_path}", file=sys.stderr)
        print("hint: run with --capture or scrot first", file=sys.stderr)
        return 1

    if args.prompt:
        # Custom prompt path — single API call, minimal parsing
        log("custom prompt: single API call", quiet=args.quiet)
        try:
            data = chat_completion(
                api_base=args.api_base,
                api_key=api_key,
                model=args.model,
                prompt=args.prompt,
                image_path=image_path,
                timeout=args.timeout,
                quiet=args.quiet,
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
            log(f"wrote {args.output}", quiet=args.quiet)
        else:
            print(content)
        return 0

    try:
        result = analyze_image(
            image_path=image_path,
            api_base=args.api_base,
            api_key=api_key,
            model=args.model,
            timeout=args.timeout,
            quiet=args.quiet,
            retry_coords=not args.no_retry,
            known_cursor=known_cursor,
            calibrate=calibrate and known_cursor is not None,
        )
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"error: HTTP {e.code}: {body}", file=sys.stderr)
        return 1
    except urllib.error.URLError as e:
        print(f"error: {e.reason}", file=sys.stderr)
        return 1

    log(f"step 4/4: done — {format_summary(result)}", quiet=args.quiet)

    if args.raw:
        print(json.dumps(result_to_json(result), ensure_ascii=False, indent=2))
        return 0

    if args.json:
        print(json.dumps(result_to_json(result), ensure_ascii=False, indent=2))
        return 0

    content = result.raw_markdown
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(content)
            if not content.endswith("\n"):
                f.write("\n")
        log(f"wrote {args.output}", quiet=args.quiet)
        print(format_summary(result))
    else:
        print(content)
        if result.targets:
            print(f"\n--- parsed ({result.coords_source}) ---", file=sys.stderr)
            for t in result.targets:
                print(
                    f"  {t.label}: bbox={t.bbox} click={t.click}",
                    file=sys.stderr,
                )
            nxt = pick_next_target(result)
            if nxt:
                ux, uy = effective_click(nxt, result)
                print(
                    f"recommended: {nxt.label} → dosbox_mouse -a move -p {ux} {uy} --sync",
                    file=sys.stderr,
                )
                if result.cursor.active:
                    print(
                        f"  (calibrated from raw {nxt.click}; offset {result.cursor.offset})",
                        file=sys.stderr,
                    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
