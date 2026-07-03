"""Terminal-native shader backdrop with cached animation frames.

Pure logic — no widget dependencies. Precomputes a small loop of dither rows
keyed by terminal size, shader mode, and theme palette, then serves frames by
phase index so run-mode backdrops animate at ~1–2 FPS without per-tick field
recomputation.
"""

from __future__ import annotations

import math
from typing import Callable, Dict, List, Literal, Sequence, Tuple

from rich.text import Text

from typatro.src.dither import DITHER_CHARS, intensity_bucket, swirl_intensity

ShaderMode = Literal["plasma", "metaballs", "low_power", "swirl"]

#: Frames per cached loop; paired with widget tick interval for smooth-enough motion.
FRAME_COUNT = 16

#: Seconds spanned by one full cached loop (matches ~2 FPS at 0.5 s ticks).
LOOP_SECONDS = 8.0

IntensityFn = Callable[[int, int, int, int, float], float]

_frame_cache: Dict[Tuple[int, int, ShaderMode, Tuple[str, ...]], List[List[Text]]] = {}


def clear_frame_cache() -> None:
    """Drop all cached shader frames (tests, hot reload)."""
    _frame_cache.clear()


def plasma_intensity(x: int, y: int, width: int, height: int, phase: float) -> float:
    """Classic multi-wave plasma field normalized to 0..1."""
    if width <= 0 or height <= 0:
        return 0.0
    nx = x / width
    ny = (y / max(height, 1)) * 2.0
    wave = (
        math.sin(nx * 10.0 + phase * 1.1)
        + math.sin(ny * 8.0 + phase * 0.85)
        + math.sin((nx + ny) * 6.0 + phase * 1.35)
        + math.sin(math.hypot(nx - 0.5, ny - 0.5) * 12.0 - phase * 1.6)
    )
    return (wave + 4.0) / 8.0


def _metaball_centers(width: int, height: int, phase: float) -> Tuple[Tuple[float, float, float], ...]:
    """Return animated blob centres as (x, y, radius) in cell coordinates."""
    span = max(width, height, 1)
    t = phase * 0.35
    return (
        (width * 0.35 + math.sin(t) * width * 0.18, height * 0.45 + math.cos(t * 0.9) * height * 0.12, span * 0.22),
        (width * 0.62 + math.cos(t * 1.1 + 1.2) * width * 0.16, height * 0.38 + math.sin(t * 0.8) * height * 0.14, span * 0.18),
        (width * 0.48 + math.sin(t * 0.7 + 2.4) * width * 0.2, height * 0.58 + math.cos(t * 1.3) * height * 0.1, span * 0.16),
    )


def metaballs_intensity(x: int, y: int, width: int, height: int, phase: float) -> float:
    """Soft metaball field normalized to 0..1."""
    if width <= 0 or height <= 0:
        return 0.0
    total = 0.0
    for cx, cy, radius in _metaball_centers(width, height, phase):
        dx = (x - cx) / max(width, 1)
        dy = ((y - cy) * 2.0) / max(height, 1)
        dist_sq = dx * dx + dy * dy + 0.002
        total += (radius / max(width, height, 1)) ** 2 / dist_sq
    return max(0.0, min(1.0, total / 2.8))


def low_power_intensity(x: int, y: int, width: int, height: int, phase: float) -> float:
    """Cheaper swirl variant with slower phase for low-power terminals."""
    return swirl_intensity(x, y, width, height, phase * 0.45)


def intensity_for_mode(mode: ShaderMode) -> IntensityFn:
    """Resolve the field function for a shader mode."""
    if mode == "plasma":
        return plasma_intensity
    if mode == "metaballs":
        return metaballs_intensity
    if mode == "low_power":
        return low_power_intensity
    if mode == "swirl":
        return swirl_intensity
    raise ValueError(f"unknown shader mode: {mode!r}")


def default_mode_for_size(width: int, height: int) -> ShaderMode:
    """Pick a visually rich but cheap default for the terminal grid."""
    cells = width * height
    if cells <= 2400:
        return "low_power"
    if cells <= 6000:
        return "plasma"
    return "plasma"


def _phase_for_frame(frame_index: int) -> float:
    return (frame_index / FRAME_COUNT) * LOOP_SECONDS


def _build_frame(
    width: int,
    height: int,
    phase: float,
    field_fn: IntensityFn,
    bucket_styles: Sequence[str],
) -> List[Text]:
    lines: List[Text] = []
    for y in range(height):
        line = Text(no_wrap=True)
        run_bucket = -1
        run_chars: List[str] = []
        for x in range(width):
            bucket = intensity_bucket(field_fn(x, y, width, height, phase))
            if bucket != run_bucket:
                if run_chars:
                    _flush_run(line, run_bucket, run_chars, bucket_styles)
                run_bucket = bucket
                run_chars = []
            run_chars.append(DITHER_CHARS[bucket])
        if run_chars:
            _flush_run(line, run_bucket, run_chars, bucket_styles)
        lines.append(line)
    return lines


def _flush_run(
    line: Text,
    bucket: int,
    chars: List[str],
    bucket_styles: Sequence[str],
) -> None:
    if bucket <= 0:
        line.append("".join(chars))
        return
    style = bucket_styles[bucket - 1] if bucket_styles else ""
    line.append("".join(chars), style=style or None)


def _build_frames(
    width: int,
    height: int,
    mode: ShaderMode,
    styles: Sequence[str],
) -> List[List[Text]]:
    field_fn = intensity_for_mode(mode)
    bucket_styles = [
        styles[(b - 1) % len(styles)] if styles else "" for b in range(1, len(DITHER_CHARS))
    ]
    return [
        _build_frame(width, height, _phase_for_frame(index), field_fn, bucket_styles)
        for index in range(FRAME_COUNT)
    ]


def cache_key(
    width: int,
    height: int,
    mode: ShaderMode,
    styles: Sequence[str],
) -> Tuple[int, int, ShaderMode, Tuple[str, ...]]:
    return (width, height, mode, tuple(styles))


def get_cached_frames(
    width: int,
    height: int,
    mode: ShaderMode,
    styles: Sequence[str],
) -> List[List[Text]]:
    """Return the cached frame loop, building it lazily on first use."""
    if width <= 0 or height <= 0:
        return []
    key = cache_key(width, height, mode, styles)
    frames = _frame_cache.get(key)
    if frames is None:
        frames = _build_frames(width, height, mode, styles)
        _frame_cache[key] = frames
    return frames


def frame_index_for_phase(phase: float) -> int:
    """Map monotonic phase seconds onto a cached frame index."""
    if LOOP_SECONDS <= 0:
        return 0
    normalized = (phase % LOOP_SECONDS) / LOOP_SECONDS
    return min(FRAME_COUNT - 1, int(normalized * FRAME_COUNT))


def render_shader_lines(
    width: int,
    height: int,
    phase: float,
    styles: Sequence[str],
    mode: ShaderMode | None = None,
) -> List[Text]:
    """Render one shader frame as Rich Text rows."""
    if width <= 0 or height <= 0:
        return []
    resolved_mode = mode or default_mode_for_size(width, height)
    frames = get_cached_frames(width, height, resolved_mode, styles)
    if not frames:
        return []
    return frames[frame_index_for_phase(phase)]


class TerminalShader:
    """Widget-friendly cache wrapper keyed by size, palette, and mode."""

    def __init__(self, mode: ShaderMode | None = None) -> None:
        self._mode = mode
        self._width = 0
        self._height = 0
        self._styles: Tuple[str, ...] = ()
        self._frames: List[List[Text]] = []

    @property
    def mode(self) -> ShaderMode | None:
        return self._mode

    def configure(
        self,
        width: int,
        height: int,
        styles: Sequence[str],
        mode: ShaderMode | None = None,
    ) -> None:
        """Invalidate and rebuild lazily when size, palette, or mode changes."""
        resolved_mode = mode if mode is not None else (
            self._mode or default_mode_for_size(width, height)
        )
        style_tuple = tuple(styles)
        if (
            width == self._width
            and height == self._height
            and style_tuple == self._styles
            and resolved_mode == self._mode
            and self._frames
        ):
            return
        self._width = width
        self._height = height
        self._styles = style_tuple
        self._mode = resolved_mode
        self._frames = get_cached_frames(width, height, resolved_mode, styles)

    def render(self, phase: float) -> List[Text]:
        """Return cached lines for the given animation phase."""
        if not self._frames:
            return []
        index = frame_index_for_phase(phase)
        return self._frames[index]
