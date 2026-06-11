"""Animated swirling dither backdrop, Balatro main-menu style."""

import time

from rich.console import Group, RenderableType
from rich.style import Style
from textual.widget import Widget

from typatro.src import config_parser
from typatro.src.balatro_experience import is_balatro_experience
from typatro.src.dither import render_lines as render_swirl_lines
from typatro.src.dither_image import render_lines_for_theme
from typatro.src.dither_poi import ZONE_COUNT, is_poi_theme


class DitherBackground(Widget, can_focus=False):
    """Slowly swirling field of dither characters in theme colors.

    Balatro and most themes use a soft spiral swirl. Bathyn and Veridia use
    POI Studio reference art downscaled to the terminal grid with animated
    grain layered on top (falls back to procedural POI grain if assets fail).
    """

    DEFAULT_CSS = """
    DitherBackground {
        width: 100%;
        height: 100%;
    }
    """

    COMPONENT_CLASSES = {
        "--dither-dim",
        "--dither-mid",
        "--dither-bright",
        "--dither-shadow",
        "--dither-teal",
        "--dither-magenta",
        "--dither-gold",
        "--dither-sparkle",
    }

    TICK_INTERVAL = 0.28
    POI_TICK_INTERVAL = 0.22

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._phase = 0.0
        self._timer = None

    def on_mount(self) -> None:
        self.set_experience_active(is_balatro_experience())

    def set_experience_active(self, active: bool) -> None:
        """Show and tick only during Balatro run mode."""
        self.display = active
        if active:
            if self._timer is None:
                self._phase = time.monotonic() % 1000.0
                interval = (
                    self.POI_TICK_INTERVAL
                    if is_poi_theme(config_parser.get("theme"))
                    else self.TICK_INTERVAL
                )
                self._timer = self.set_interval(interval, self._tick)
            else:
                self._timer.resume()
            self.refresh()
        elif self._timer is not None:
            self._timer.pause()

    def on_show(self) -> None:
        if self._timer is not None and is_balatro_experience():
            self._timer.resume()

    def on_hide(self) -> None:
        if self._timer is not None:
            self._timer.pause()

    def _tick(self) -> None:
        if not is_balatro_experience() or not self.display:
            return
        interval = (
            self.POI_TICK_INTERVAL
            if is_poi_theme(config_parser.get("theme"))
            else self.TICK_INTERVAL
        )
        self._phase += interval
        if self.size.width > 0:
            self.refresh()

    @staticmethod
    def _style_str(style: Style) -> str:
        if style.color is not None and style.color.triplet is not None:
            triplet = style.color.triplet
            return "#{:02x}{:02x}{:02x}".format(triplet.red, triplet.green, triplet.blue)
        if style.color is not None:
            return style.color.name or ""
        return ""

    def _swirl_styles(self) -> list[str]:
        return [
            self._style_str(self.get_component_rich_style("--dither-dim")),
            self._style_str(self.get_component_rich_style("--dither-mid")),
            self._style_str(self.get_component_rich_style("--dither-bright")),
        ]

    def _poi_zone_styles(self) -> list[str]:
        keys = (
            "--dither-shadow",
            "--dither-teal",
            "--dither-magenta",
            "--dither-gold",
            "--dither-sparkle",
        )
        return [
            self._style_str(self.get_component_rich_style(keys[i % len(keys)]))
            for i in range(ZONE_COUNT)
        ]

    def render(self) -> RenderableType:
        width = self.size.width
        height = self.size.height
        if width <= 0 or height <= 0:
            return ""

        theme = config_parser.get("theme")
        if is_poi_theme(theme):
            lines = render_lines_for_theme(
                theme,
                width,
                height,
                self._phase,
                self._poi_zone_styles(),
            )
        else:
            lines = render_swirl_lines(width, height, self._phase, self._swirl_styles())
        return Group(*lines)
