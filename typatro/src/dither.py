"""Balatro-style swirling dither field for animated TUI backdrops.

Pure logic — no widget dependencies — so it stays unit-testable. Widgets
drive ``render_lines`` from a Textual interval timer, passing a phase that
advances over time, and paint the result with Rich Text (run-grouped styles,
never per-cell widgets).
"""

from __future__ import annotations

import math
from typing import List, Sequence

from rich.text import Text

#: Intensity ramp, dimmest to brightest. Index 0 renders as empty space.
DITHER_CHARS = (" ", "\u2591", "\u2592", "\u2593")  # ' ' ░ ▒ ▓

#: Thresholds (over normalized 0..1 intensity) for each non-space bucket.
_BUCKET_THRESHOLDS = (0.50, 0.70, 0.88)


def swirl_intensity(x: int, y: int, width: int, height: int, phase: float) -> float:
    """Normalized (0..1) intensity of the swirl field at a cell.

    Combines a rotating spiral around the centre with a slow diagonal wave,
    approximating Balatro's liquid background. ``y`` is doubled to compensate
    for terminal cell aspect ratio.
    """
    if width <= 0 or height <= 0:
        return 0.0
    dx = (x - width / 2.0) / width
    dy = (y - height / 2.0) * 2.0 / max(height, 1)
    radius = math.sqrt(dx * dx + dy * dy)
    angle = math.atan2(dy, dx)

    spiral = math.sin(radius * 7.0 - phase * 1.4 + angle * 2.0)
    wave = math.sin(x * 0.11 + y * 0.23 + phase * 0.6)
    return (spiral + wave + 2.0) / 4.0


def intensity_bucket(value: float) -> int:
    """Map a 0..1 intensity onto a DITHER_CHARS index."""
    for index, threshold in enumerate(_BUCKET_THRESHOLDS):
        if value < threshold:
            return index
    return len(_BUCKET_THRESHOLDS)


def render_lines(
    width: int,
    height: int,
    phase: float,
    styles: Sequence[str],
) -> List[Text]:
    """Render the swirl field as one Rich Text per row.

    ``styles`` supplies the style for each non-space bucket (cycled if it is
    shorter than the bucket count). Adjacent cells in the same bucket are
    grouped into a single styled run for performance.
    """
    lines: List[Text] = []
    bucket_styles = [
        styles[(b - 1) % len(styles)] if styles else "" for b in range(1, len(DITHER_CHARS))
    ]

    for y in range(height):
        line = Text(no_wrap=True)
        run_bucket = -1
        run_chars: List[str] = []
        for x in range(width):
            bucket = intensity_bucket(swirl_intensity(x, y, width, height, phase))
            if bucket != run_bucket:
                if run_chars:
                    _flush(line, run_bucket, run_chars, bucket_styles)
                run_bucket = bucket
                run_chars = []
            run_chars.append(DITHER_CHARS[bucket])
        if run_chars:
            _flush(line, run_bucket, run_chars, bucket_styles)
        lines.append(line)
    return lines


def _flush(line: Text, bucket: int, chars: List[str], bucket_styles: List[str]) -> None:
    style = "" if bucket <= 0 else bucket_styles[bucket - 1]
    line.append("".join(chars), style=style or None)
