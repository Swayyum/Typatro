"""Let the Balatro dither backdrop show through layout-only shells in run mode.

Design: ``DitherBackground`` fills the screen on a backdrop layer, but header,
sidebar, and game cards stay opaque/semi-opaque so nav and scores stay readable.
Only typing-column layout shells (pads, scroll chrome, content switcher) skip
painting so the swirl appears in margins and gaps — ambient background, not UI
noise behind chrome.

Textual compositors paint front-to-back; a widget that emits a full-width strip
(even spaces + inherited background) blocks every cell in its region. Layout
containers between ``ContentSwitcher`` and leaf widgets must emit empty strips
during run mode so ``DitherBackground`` on the backdrop layer remains visible
behind typing UI without ``overlay: screen``.
"""

from __future__ import annotations

from textual.geometry import Region
from textual.strip import Strip

from typatro.src.balatro_experience import is_balatro_experience

_EMPTY_STRIPS: dict[int, list[Strip]] = {}


def _empty_strips(height: int) -> list[Strip]:
    cached = _EMPTY_STRIPS.get(height)
    if cached is None:
        cached = [Strip([]) for _ in range(height)]
        _EMPTY_STRIPS[height] = cached
    return cached


class DitherPassthrough:
    """Mixin: skip painting layout shells while Balatro run mode is active."""

    def render_lines(self, crop: Region) -> list[Strip]:
        if is_balatro_experience():
            return _empty_strips(crop.height)
        return super().render_lines(crop)
