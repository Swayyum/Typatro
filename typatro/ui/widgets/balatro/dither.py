"""Animated swirling dither backdrop, Balatro main-menu style."""

import time

from rich.console import Group, RenderableType
from rich.style import Style
from textual.widget import Widget

from typatro.src.balatro_experience import is_balatro_experience
from typatro.src.dither import render_lines


class DitherBackground(Widget, can_focus=False):
    """Slowly swirling field of dither characters in theme colors.

    Renders with run-grouped Rich Text (cheap), ticks at a modest rate, and
    pauses its timer whenever the widget is hidden.
    """

    DEFAULT_CSS = """
    DitherBackground {
        width: 100%;
        height: 100%;
    }
    """

    COMPONENT_CLASSES = {"--dither-dim", "--dither-mid", "--dither-bright"}

    TICK_INTERVAL = 0.5
    TYPING_IDLE_DELAY = 0.35

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._phase = 0.0
        self._timer = None
        self._idle_timer = None

    def on_mount(self) -> None:
        self.set_experience_active(is_balatro_experience())

    def set_experience_active(self, active: bool) -> None:
        """Show and tick only during Balatro run mode."""
        self.display = active
        if active:
            if self._timer is None:
                self._phase = time.monotonic() % 1000.0
                self._timer = self.set_interval(self.TICK_INTERVAL, self._tick)
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
        self._phase += self.TICK_INTERVAL
        if self.size.width > 0:
            self.refresh()

    def on_typing_activity(self) -> None:
        """Pause backdrop animation while the user is typing (keeps input responsive)."""
        if not is_balatro_experience() or not self.display:
            return
        if self._timer is not None:
            self._timer.pause()
        if self._idle_timer is not None:
            self._idle_timer.stop()
        self._idle_timer = self.set_timer(
            self.TYPING_IDLE_DELAY,
            self._resume_after_typing,
            name="dither-typing-idle",
        )

    def _resume_after_typing(self) -> None:
        self._idle_timer = None
        if self._timer is not None and is_balatro_experience() and self.display:
            self._timer.resume()

    @staticmethod
    def _style_str(style: Style) -> str:
        if style.color is not None and style.color.triplet is not None:
            triplet = style.color.triplet
            return "#{:02x}{:02x}{:02x}".format(triplet.red, triplet.green, triplet.blue)
        if style.color is not None:
            return style.color.name or ""
        return ""

    def render(self) -> RenderableType:
        width = self.size.width
        height = self.size.height
        if width <= 0 or height <= 0:
            return ""

        styles = [
            self._style_str(self.get_component_rich_style("--dither-dim")),
            self._style_str(self.get_component_rich_style("--dither-mid")),
            self._style_str(self.get_component_rich_style("--dither-bright")),
        ]
        return Group(*render_lines(width, height, self._phase, styles))
