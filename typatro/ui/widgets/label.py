import time
from typing import Optional

from rich.console import RenderableType
from textual.reactive import reactive
from textual.widget import Widget

from typatro.src.slot_machine import LogoReelEngine
from typatro.ui.events import SetScreen


class NavItemBase(Widget):
    """
    Base Widget for Header NavItems
    """

    DEFAULT_CSS = """
    NavItemBase {
        content-align: center middle;
        height: auto;
        width: auto;
        padding: 0 1;
    }
    """

    def __init__(self, text: str, screen_name: Optional[str] = None) -> None:
        super().__init__()
        self.text = text
        self.screen_name = screen_name

    def on_click(self) -> None:
        if self.screen_name:
            self.post_message(SetScreen(self.screen_name))

    def render(self) -> RenderableType:
        return self.text


class Banner(NavItemBase):
    """
    Vegas-style rainbow logo: spaced rainbow letters with per-column reels
    that spin, decelerate, and lock left-to-right.
    """

    DEFAULT_CSS = """
    Banner {
        height: 100%;
        width: auto;
        content-align: left middle;
        padding: 0;
    }
    """

    SPIN_INTERVAL = 0.07
    RAINBOW_INTERVAL = 0.033  # ~30fps color cycle while idle

    is_tall = reactive(True, layout=True, always_update=True)

    def __init__(self, text: str, screen_name: Optional[str] = None) -> None:
        super().__init__(text, screen_name)
        self._engine = LogoReelEngine(target=text)

    def get_content_width(self, container, viewport) -> int:
        return self._engine.logo_width() + 2  # + horizontal padding

    def get_content_height(self, container, viewport, width: int) -> int:
        return 3 if self.is_tall else 1

    def on_mount(self) -> None:
        self._spin_timer = self.set_interval(self.SPIN_INTERVAL, self._spin_tick)
        self._rainbow_timer = self.set_interval(self.RAINBOW_INTERVAL, self._rainbow_tick)

    def _spin_tick(self) -> None:
        if self._engine.done:
            return
        self._engine.tick()
        self.refresh()

    def _rainbow_tick(self) -> None:
        self.refresh()

    def respin(self) -> None:
        """Restart the logo reel intro (used on screen changes / click)."""
        self._engine.reset()
        self._spin_timer.resume()
        self.refresh()

    def on_click(self) -> None:
        self.respin()
        super().on_click()

    def watch_is_tall(self, value: bool) -> None:
        self.styles.height = "100%"

    def render(self) -> RenderableType:
        phase = time.monotonic()
        bar_width = self.size.width if self.size.width > 0 else None
        return self._engine.render_logo(
            phase,
            marquee=self.is_tall,
            bar_width=bar_width,
        )


class NavItem(NavItemBase):
    """
    Just a label widget with a callback
    """
