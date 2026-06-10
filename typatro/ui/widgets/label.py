from typing import Optional
from rich.console import RenderableType
from rich.text import Text
from textual.reactive import reactive
from textual.widget import Widget
from typatro.src import generate_figlet
from typatro.src.slot_machine import ReelSpin
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
    Big-font title with a slot machine reel-spin intro: letters cycle
    through random symbols and lock in left to right.
    """

    DEFAULT_CSS = """
    Banner {
        height: 100%;
    }
    """

    SPIN_INTERVAL = 0.06

    is_tall = reactive(True, layout=True, always_update=True)

    def __init__(self, text: str, screen_name: Optional[str] = None) -> None:
        super().__init__(text, screen_name)
        self._reel = ReelSpin(target=text)
        self._display = text

    def on_mount(self) -> None:
        self._spin_timer = self.set_interval(self.SPIN_INTERVAL, self._spin_tick)

    def _spin_tick(self) -> None:
        self._display = self._reel.tick()
        if self._reel.done:
            self._display = self.text
            self._spin_timer.pause()
        self.refresh()

    def respin(self) -> None:
        """Restart the reel-spin intro (used on screen changes)."""
        self._reel = ReelSpin(target=self.text)
        self._spin_timer.resume()

    def on_click(self) -> None:
        self.respin()
        super().on_click()

    def watch_is_tall(self, value: bool) -> None:
        self.styles.height = "5" if value else "3"

    def render(self) -> RenderableType:
        spinning = not self._reel.done
        source = self._display
        rendered = generate_figlet(source) if self.is_tall else source.upper()
        if spinning:
            return Text(rendered, style="bold")
        return rendered


class NavItem(NavItemBase):
    """
    Just a label widget with a callback
    """
