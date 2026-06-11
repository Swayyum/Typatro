"""POI Studio–inspired grainy dither field for Bathyn / Veridia themes.

Organic color zones (teal waves, magenta hills, cream highlights) with heavy
stochastic grain, approximating POI Studio brand art. Pure logic — no widget
dependencies — so it stays unit-testable.
"""

from __future__ import annotations

import math
from typing import List, Sequence

from rich.text import Text

from typatro.src.dither import DITHER_CHARS

#: Themes that use the POI grain algorithm and zone-colored dither.
POI_THEMES = frozenset({"bathyn", "veridia"})

#: Landscape zone indices returned by ``poi_zone``.
ZONE_SHADOW = 0
ZONE_TEAL = 1
ZONE_MAGENTA = 2
ZONE_GOLD = 3
ZONE_SPARKLE = 4
ZONE_COUNT = 5

#: Thresholds (over normalized 0..1 grain) for each non-space bucket.
_BUCKET_THRESHOLDS = (0.52, 0.72, 0.88)


def is_poi_theme(theme: str | None) -> bool:
    """Return True when ``theme`` should use POI grain dither."""
    return theme in POI_THEMES


def _hash_noise(x: int, y: int, phase: float) -> float:
    """Deterministic pseudo-random grain in 0..1 (stochastic dither feel)."""
    seed = (
        x * 374761393
        + y * 668265263
        + int(phase * 97.0) * 1274126177
    ) & 0xFFFFFFFF
    seed = ((seed >> 16) ^ seed) * 0x45D9F3B
    seed = ((seed >> 16) ^ seed) * 0x45D9F3B
    seed = (seed >> 16) ^ seed
    return (seed & 0xFFFF) / 65535.0


def _landscape(x: int, y: int, width: int, height: int, phase: float) -> float:
    """Organic rolling-hill / wave field in 0..1."""
    if width <= 0 or height <= 0:
        return 0.0
    nx = x / width
    ny = (y / max(height, 1)) * 2.0

    drift = phase * 0.18
    hills = (
        math.sin(nx * 3.8 + drift) * 0.35
        + math.sin(nx * 2.1 - drift * 0.7 + ny * 0.45) * 0.28
        + math.sin((nx + ny * 0.6) * 2.6 + drift * 0.5) * 0.22
    )
    waves = math.sin(ny * 4.5 - drift * 1.3 + nx * 1.8) * 0.38
    swell = math.sin(drift * 0.9 + nx * 1.2) * 0.15
    raw = hills + waves + swell
    return max(0.0, min(1.0, (raw + 0.8) / 2.2))


def poi_zone(x: int, y: int, width: int, height: int, phase: float) -> int:
    """Map a cell onto one of the POI color zones."""
    field = _landscape(x, y, width, height, phase)
    sparkle_gate = _hash_noise(x + 17, y + 31, phase)
    if field > 0.86 and sparkle_gate > 0.82:
        return ZONE_SPARKLE
    if field < 0.22:
        return ZONE_SHADOW
    if field < 0.42:
        return ZONE_TEAL
    if field < 0.62:
        return ZONE_MAGENTA
    if field < 0.82:
        return ZONE_GOLD
    return ZONE_MAGENTA


def poi_intensity(x: int, y: int, width: int, height: int, phase: float) -> float:
    """Normalized (0..1) combined landscape + grain."""
    if width <= 0 or height <= 0:
        return 0.0
    landscape = _landscape(x, y, width, height, phase)
    grain = _hash_noise(x, y, phase)
    scanline = 0.88 if y % 2 else 1.0
    return max(0.0, min(1.0, (landscape * 0.55 + grain * 0.45) * scanline))


def poi_intensity_bucket(value: float) -> int:
    """Map a 0..1 intensity onto a DITHER_CHARS index for POI grain."""
    for index, threshold in enumerate(_BUCKET_THRESHOLDS):
        if value < threshold:
            return index
    return len(_BUCKET_THRESHOLDS)


def render_lines(
    width: int,
    height: int,
    phase: float,
    zone_styles: Sequence[str],
) -> List[Text]:
    """Render the grain field as one Rich Text per row.

    ``zone_styles`` supplies the style for each POI zone (cycled if shorter than
    ``ZONE_COUNT``). Adjacent cells sharing zone and bucket are grouped.
    """
    lines: List[Text] = []
    styles = [
        zone_styles[z % len(zone_styles)] if zone_styles else ""
        for z in range(ZONE_COUNT)
    ]

    for y in range(height):
        line = Text(no_wrap=True)
        run_key = (-1, -1)
        run_chars: List[str] = []
        for x in range(width):
            zone = poi_zone(x, y, width, height, phase)
            bucket = poi_intensity_bucket(poi_intensity(x, y, width, height, phase))
            key = (zone, bucket)
            if key != run_key:
                if run_chars:
                    _flush(line, run_key, run_chars, styles)
                run_key = key
                run_chars = []
            run_chars.append(DITHER_CHARS[bucket])
        if run_chars:
            _flush(line, run_key, run_chars, styles)
        lines.append(line)
    return lines


def _flush(
    line: Text,
    key: tuple[int, int],
    chars: List[str],
    zone_styles: List[str],
) -> None:
    zone, bucket = key
    if bucket <= 0:
        line.append("".join(chars))
        return
    style = zone_styles[zone] if zone < len(zone_styles) else ""
    line.append("".join(chars), style=style or None)
