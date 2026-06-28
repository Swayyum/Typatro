"""Joker card illustration rendering from bundled JPEG assets."""

from __future__ import annotations

import base64
import json
import os
from importlib.resources import files
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Tuple

from rich.console import Console, ConsoleOptions, RenderResult
from rich.segment import Segment
from rich.style import Style
from rich.text import Text

RGB = Tuple[int, int, int]
Grid = List[List[RGB]]

# Cream card face — used when letterboxing full-card JPEGs.
_CARD_BG_RGB: RGB = (246, 241, 227)
_CARD_BG_HEX = "#f6f1e3"

# Joker id → filename under ``typatro/assets/jokers/``.
JOKER_IMAGE_FILES: Dict[str, str] = {
    "joker": "joker.jpeg",
    "greedy": "greedy.jpeg",
    "lusty": "lusty.jpeg",
    "wrathful": "wrathful.jpeg",
    "banner": "banner.jpeg",
    "mystic": "mystic.jpeg",
}

_PREBAKED_ART_SUFFIX = ".art.json"

# Upper half block: Rich uses bgcolor for the top pixel, color for the bottom.
_HALF_BLOCK = "▀"

# Typical terminal cell aspect (width:height ≈ 1:2).
_CELL_PX_W = 8
_CELL_PX_H = 16

_sample_cache: Dict[Tuple[str, int, int], Grid] = {}
_bytes_cache: Dict[Tuple[str, int, int], bytes] = {}
_prebaked_cache: Dict[str, List[Text]] = {}


def clear_sample_cache() -> None:
    _sample_cache.clear()
    _bytes_cache.clear()
    _prebaked_cache.clear()


def has_prebaked_art(joker_id: str) -> bool:
    return prebaked_art_path(joker_id) is not None


def prebaked_art_path(joker_id: str) -> Path | None:
    if joker_id not in JOKER_IMAGE_FILES:
        return None
    path = Path(files("typatro.assets.jokers").joinpath(f"{joker_id}{_PREBAKED_ART_SUFFIX}"))
    return path if path.is_file() else None


def _rows_to_text_lines(rows: List[List[List[str | None]]]) -> List[Text]:
    lines: List[Text] = []
    for row in rows:
        line = Text(no_wrap=True)
        for char, fg, bg in row:
            style_kwargs: dict[str, str] = {}
            if fg:
                style_kwargs["color"] = fg
            if bg:
                style_kwargs["bgcolor"] = bg
            line.append(
                char,
                style=Style(**style_kwargs) if style_kwargs else None,
            )
        lines.append(line)
    return lines


def load_prebaked_art_lines(
    joker_id: str,
    width: int,
    line_count: int,
) -> List[Text] | None:
    """Return committed chafa block art — universal across modern terminals."""
    if joker_id in _prebaked_cache:
        cached = _prebaked_cache[joker_id]
        if len(cached) == line_count and cached[0].cell_len == width:
            return cached

    path = prebaked_art_path(joker_id)
    if path is None:
        return None

    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("width") != width or payload.get("height") != line_count:
        return None

    lines = _rows_to_text_lines(payload["rows"])
    _prebaked_cache[joker_id] = lines
    return lines


def has_joker_image(joker_id: str) -> bool:
    return joker_id in JOKER_IMAGE_FILES and joker_image_path(joker_id) is not None


def joker_image_path(joker_id: str) -> Path | None:
    filename = JOKER_IMAGE_FILES.get(joker_id)
    if not filename:
        return None
    path = Path(files("typatro.assets.jokers").joinpath(filename))
    return path if path.is_file() else None


def inline_images_enabled() -> bool:
    """Inline JPEG graphics are opt-in — they glitch in many hosts (Ghostty, tmux)."""
    return os.environ.get("TYPATRO_INLINE_IMAGES", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def terminal_image_protocol() -> str | None:
    """Return the active inline-image protocol for this terminal, if any."""
    if not inline_images_enabled():
        return None

    term = os.environ.get("TERM", "")
    term_program = os.environ.get("TERM_PROGRAM", "")
    term_program_version = os.environ.get("TERM_PROGRAM_VERSION", "")

    if os.environ.get("KITTY_WINDOW_ID"):
        return "kitty"
    if term_program in {"kitty", "WezTerm", "ghostty"}:
        return "kitty"
    if "ghostty" in term.lower() or "wezterm" in term.lower():
        return "kitty"
    if os.environ.get("LC_TERMINAL") == "iTerm2" or term_program == "iTerm.app":
        return "iterm"
    if term_program == "Apple_Terminal" and term_program_version:
        # Terminal.app gained iTerm-style image support in recent macOS releases.
        return "iterm"
    return None


def _pixel_size(cols: int, rows: int) -> Tuple[int, int]:
    return max(1, cols * _CELL_PX_W), max(1, rows * _CELL_PX_H)


def prepare_joker_image_bytes(joker_id: str, pixel_w: int, pixel_h: int) -> bytes | None:
    """Resize a bundled JPEG for inline terminal display."""
    if pixel_w <= 0 or pixel_h <= 0:
        return None

    cache_key = (joker_id, pixel_w, pixel_h)
    if cache_key in _bytes_cache:
        return _bytes_cache[cache_key]

    path = joker_image_path(joker_id)
    if path is None:
        return None

    try:
        from PIL import Image
    except ImportError:
        return None

    with Image.open(path) as img:
        img = img.convert("RGB")
        scale = min(pixel_w / img.width, pixel_h / img.height)
        new_w = max(1, int(img.width * scale))
        new_h = max(1, int(img.height * scale))
        resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (pixel_w, pixel_h), _CARD_BG_RGB)
        offset_x = (pixel_w - new_w) // 2
        offset_y = (pixel_h - new_h) // 2
        canvas.paste(resized, (offset_x, offset_y))
        buf = BytesIO()
        canvas.save(buf, format="JPEG", quality=88)
        data = buf.getvalue()

    _bytes_cache[cache_key] = data
    return data


def build_kitty_image_sequence(
    image_data: bytes,
    *,
    cols: int,
    rows: int,
    pixel_w: int,
    pixel_h: int,
    x: int = 0,
    y: int = 0,
) -> str:
    """Build a Kitty graphics protocol escape placing a JPEG at ``(x, y)`` cells."""
    payload = base64.standard_b64encode(image_data).decode("ascii")
    return (
        f"\x1b_Ga=T,f=100,s={pixel_w},v={pixel_h},c={cols},r={rows},"
        f"X={x},Y={y},C=1,t=d;{payload}\x1b\\"
    )


def build_iterm_image_sequence(
    image_data: bytes,
    *,
    pixel_w: int,
    pixel_h: int,
) -> str:
    """Build an iTerm2 inline image escape for the current cursor cell."""
    payload = base64.standard_b64encode(image_data).decode("ascii")
    return (
        f"\x1b]1337;File=inline=1;width={pixel_w}px;height={pixel_h}px;"
        f"preserveAspectRatio=1:{payload}\x07"
    )


class TerminalJokerArt:
    """Rich renderable that embeds a real JPEG via Kitty/iTerm graphics."""

    def __init__(
        self,
        sequence: str,
        *,
        inner_width: int,
        art_rows: int,
    ) -> None:
        self.sequence = sequence
        self.inner_width = inner_width
        self.art_rows = art_rows

    def __rich_console__(
        self,
        console: Console,
        options: ConsoleOptions,
    ) -> RenderResult:
        yield Segment(self.sequence, control=True)
        body = Style(bgcolor=_CARD_BG_HEX)
        for row in range(self.art_rows):
            yield Segment(" " * self.inner_width, body)
            if row < self.art_rows - 1:
                yield Segment("\n")


def render_joker_terminal_art(
    joker_id: str,
    inner_width: int,
    art_rows: int,
    *,
    screen_x: int,
    screen_y: int,
) -> TerminalJokerArt | None:
    """Return a terminal-graphics renderable when explicitly enabled and supported."""
    if not inline_images_enabled():
        return None

    protocol = terminal_image_protocol()
    if protocol is None:
        return None

    pixel_w, pixel_h = _pixel_size(inner_width, art_rows)
    image_data = prepare_joker_image_bytes(joker_id, pixel_w, pixel_h)
    if image_data is None:
        return None

    if protocol == "kitty":
        sequence = build_kitty_image_sequence(
            image_data,
            cols=inner_width,
            rows=art_rows,
            pixel_w=pixel_w,
            pixel_h=pixel_h,
            x=screen_x + 1,
            y=screen_y + 1,
        )
    else:
        sequence = build_iterm_image_sequence(
            image_data,
            pixel_w=pixel_w,
            pixel_h=pixel_h,
        )

    return TerminalJokerArt(sequence, inner_width=inner_width, art_rows=art_rows)


def sample_joker_grid(joker_id: str, width: int, height: int) -> Grid | None:
    """Downscale a full-card JPEG with contain-fit onto a cream canvas."""
    if width <= 0 or height <= 0:
        return None

    cache_key = (joker_id, width, height)
    if cache_key in _sample_cache:
        return _sample_cache[cache_key]

    path = joker_image_path(joker_id)
    if path is None:
        return None

    try:
        from PIL import Image
    except ImportError:
        return None

    with Image.open(path) as img:
        img = img.convert("RGB")
        scale = min(width / img.width, height / img.height)
        new_w = max(1, int(img.width * scale))
        new_h = max(1, int(img.height * scale))
        resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (width, height), _CARD_BG_RGB)
        offset_x = (width - new_w) // 2
        offset_y = (height - new_h) // 2
        canvas.paste(resized, (offset_x, offset_y))
        pixels = list(canvas.get_flattened_data())
        grid = [
            [pixels[y * width + x] for x in range(width)]
            for y in range(height)
        ]

    _sample_cache[cache_key] = grid
    return grid


def _rgb_hex(rgb: RGB) -> str:
    return "#{:02x}{:02x}{:02x}".format(rgb[0], rgb[1], rgb[2])


def art_color_variance(joker_id: str, width: int, rows: int) -> int:
    """Count horizontally adjacent color transitions in sampled art (detail proxy)."""
    pixel_h = rows * 2
    grid = sample_joker_grid(joker_id, width, pixel_h)
    if grid is None:
        return 0
    transitions = 0
    for row in grid:
        for x in range(len(row) - 1):
            if row[x] != row[x + 1]:
                transitions += 1
    return transitions


def render_joker_art_lines(
    joker_id: str,
    width: int,
    line_count: int,
    phase: float = 0.0,
) -> List[Text] | None:
    """Render card art as truecolor half-block pixels (2 terminal rows per cell row)."""
    del phase  # static art — animation was noisy at pick-card size
    if line_count <= 0 or width <= 0:
        return None

    pixel_w = width
    pixel_h = line_count * 2
    grid = sample_joker_grid(joker_id, pixel_w, pixel_h)
    if grid is None:
        return None

    lines: List[Text] = []
    for row in range(line_count):
        line = Text(no_wrap=True)
        top_y = row * 2
        bottom_y = top_y + 1
        for col in range(width):
            top_rgb = grid[top_y][col]
            bottom_rgb = grid[bottom_y][col]
            line.append(
                _HALF_BLOCK,
                style=Style(color=_rgb_hex(bottom_rgb), bgcolor=_rgb_hex(top_rgb)),
            )
        lines.append(line)
    return lines
