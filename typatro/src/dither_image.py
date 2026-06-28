"""Optional image-backed dither for themed run backdrops.

Downscales bundled reference art to the terminal grid and renders with Rich
dither characters tinted by sampled RGB. Falls back to procedural grain when
Pillow is unavailable or no asset is configured.
"""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from rich.text import Text

from typatro.src.dither import DITHER_CHARS
from typatro.src.dither_poi import _hash_noise, is_poi_theme

RGB = Tuple[int, int, int]
Grid = List[List[RGB]]

#: Theme → bundled asset filename under ``typatro.assets``.
POI_BACKGROUND_ASSETS: dict[str, str] = {}

#: Downscaled RGB grids keyed by (theme, width, height).
_sample_cache: Dict[Tuple[str, int, int], Grid] = {}

#: Thresholds for image+luminance+grain composite (slightly denser than swirl).
_IMAGE_BUCKET_THRESHOLDS = (0.48, 0.68, 0.86)


def clear_sample_cache() -> None:
    """Drop cached downscales (tests, theme hot-reload)."""
    _sample_cache.clear()


def poi_background_path(theme: str) -> Path | None:
    """Return the bundled PNG path for a POI theme, or None."""
    if not is_poi_theme(theme):
        return None
    filename = POI_BACKGROUND_ASSETS.get(theme)
    if filename is None:
        return None
    return Path(files("typatro.assets").joinpath(filename))


def _cover_crop_box(
    img_width: int,
    img_height: int,
    target_width: int,
    target_height: int,
) -> Tuple[int, int, int, int]:
    """Box that crops the source image to cover ``target`` aspect ratio."""
    if img_width <= 0 or img_height <= 0 or target_width <= 0 or target_height <= 0:
        return (0, 0, img_width, img_height)
    target_aspect = target_width / target_height
    source_aspect = img_width / img_height
    if source_aspect > target_aspect:
        crop_w = int(img_height * target_aspect)
        left = (img_width - crop_w) // 2
        return (left, 0, left + crop_w, img_height)
    crop_h = int(img_width / target_aspect)
    top = (img_height - crop_h) // 2
    return (0, top, img_width, top + crop_h)


def sample_image_grid(theme: str, width: int, height: int) -> Grid | None:
    """Downscale the POI reference image to a ``width`` × ``height`` RGB grid."""
    if width <= 0 or height <= 0 or not is_poi_theme(theme):
        return None

    cache_key = (theme, width, height)
    if cache_key in _sample_cache:
        return _sample_cache[cache_key]

    path = poi_background_path(theme)
    if path is None or not path.is_file():
        return None

    try:
        from PIL import Image
    except ImportError:
        return None

    with Image.open(path) as img:
        rgb = img.convert("RGB")
        box = _cover_crop_box(rgb.width, rgb.height, width, height)
        cropped = rgb.crop(box)
        resized = cropped.resize((width, height), Image.Resampling.LANCZOS)
        pixels = resized.load()
        grid: Grid = [
            [pixels[x, y] for x in range(width)] for y in range(height)
        ]

    _sample_cache[cache_key] = grid
    return grid


def _luminance(rgb: RGB) -> float:
    r, g, b = rgb
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255.0


def _image_intensity_bucket(value: float) -> int:
    for index, threshold in enumerate(_IMAGE_BUCKET_THRESHOLDS):
        if value < threshold:
            return index
    return len(_IMAGE_BUCKET_THRESHOLDS)


def _modulate_rgb(rgb: RGB, bucket: int, grain: float) -> str:
    """Return a Rich-compatible ``#rrggbb`` tint for this cell."""
    r, g, b = rgb
    density = 0.72 + 0.28 * (bucket / max(len(DITHER_CHARS) - 1, 1))
    grain_boost = 0.92 + 0.08 * grain
    scale = density * grain_boost
    return "#{:02x}{:02x}{:02x}".format(
        min(255, int(r * scale)),
        min(255, int(g * scale)),
        min(255, int(b * scale)),
    )


def composite_intensity(
    x: int,
    y: int,
    luma: float,
    phase: float,
) -> float:
    """Blend image luminance with animated grain and a light ordered dither."""
    grain = _hash_noise(x, y, phase)
    ordered = ((x + int(phase * 2.5)) % 4 + (y % 4)) % 4 / 3.0
    scanline = 0.9 if y % 2 else 1.0
    raw = luma * 0.52 + grain * 0.38 + ordered * 0.1
    return max(0.0, min(1.0, raw * scanline))


def render_lines(
    width: int,
    height: int,
    phase: float,
    rgb_grid: Grid,
) -> List[Text]:
    """Render image-tinted dither rows from a pre-sampled RGB grid."""
    lines: List[Text] = []
    for y in range(height):
        line = Text(no_wrap=True)
        row = rgb_grid[y] if y < len(rgb_grid) else []
        run_key: Tuple[int, str] | None = None
        run_chars: List[str] = []

        for x in range(width):
            rgb = row[x] if x < len(row) else (0, 0, 0)
            luma = _luminance(rgb)
            grain = _hash_noise(x, y, phase)
            bucket = _image_intensity_bucket(composite_intensity(x, y, luma, phase))
            color = _modulate_rgb(rgb, bucket, grain)
            key = (bucket, color)

            if key != run_key:
                if run_chars:
                    _flush_image_run(line, run_key, run_chars)
                run_key = key
                run_chars = []
            run_chars.append(DITHER_CHARS[bucket])

        if run_chars:
            _flush_image_run(line, run_key, run_chars)
        lines.append(line)
    return lines


def _flush_image_run(
    line: Text,
    key: Tuple[int, str] | None,
    chars: List[str],
) -> None:
    if key is None:
        line.append("".join(chars))
        return
    bucket, color = key
    if bucket <= 0:
        line.append("".join(chars))
        return
    line.append("".join(chars), style=color)


def render_lines_for_theme(
    theme: str,
    width: int,
    height: int,
    phase: float,
    fallback_zone_styles: Sequence[str],
) -> List[Text]:
    """Sample (cached) and render, or fall back to procedural POI grain."""
    grid = sample_image_grid(theme, width, height)
    if grid is not None:
        return render_lines(width, height, phase, grid)

    from typatro.src.dither_poi import render_lines as render_poi_lines

    return render_poi_lines(width, height, phase, fallback_zone_styles)
