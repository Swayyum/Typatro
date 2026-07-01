from rich.console import RenderableType
from textual.app import ComposeResult, events
from textual.widget import Widget
from typatro.ui.widgets import (
    BaseWindow,
    TypingConfigStrip,
    PaletteOptions,
    Space,
    Ticker,
)
from typatro.ui.widgets.dither_passthrough import DitherPassthrough
from typatro.ui.widgets.balatro import ScorePanel, BlindCard, JokerRow
from textual.containers import VerticalScroll
from typatro.ui.events import SetScreen
from typatro.src import run_manager, config_parser
from typatro.ui.sidebar_layout import SIDEBAR_PADDING, SIDEBAR_WIDTH


class TypingScroll(VerticalScroll, can_focus=False):
    pass


class Pad(DitherPassthrough, Widget):
    """
    Pad widget for empty spaces
    """

    DEFAULT_CSS = """
    Pad.cspan3 {
        column-span: 3;
    }
    """

    def render(self) -> RenderableType:
        return ""


class GameSidebar(Widget):
    """Balatro-style left panel: blind card, round score, jokers."""

    DEFAULT_CSS = f"""
    GameSidebar {{
        layout: vertical;
        width: {SIDEBAR_WIDTH};
        height: 100%;
        padding: {SIDEBAR_PADDING} {SIDEBAR_PADDING};
    }}

    GameSidebar.hidden {{
        display: none;
    }}

    GameSidebar > BlindCard {{
        margin-bottom: 1;
    }}

    GameSidebar > ScorePanel {{
        margin-bottom: 1;
    }}
    """

    def compose(self) -> ComposeResult:
        yield BlindCard()
        yield ScorePanel()
        yield JokerRow()


class TypingArea(DitherPassthrough, Widget):
    """Main typing column: config strip, ticker, paragraph."""

    DEFAULT_CSS = """
    TypingArea {
        layout: grid;
        grid-size: 3 6;
        grid-columns: 2fr 4fr 2fr;
        grid-rows: 1 1fr 1 6 1fr 1;
        height: 100%;
        width: 1fr;
        margin: 0 1;
    }

    TypingArea > Ticker {
        text-style: bold;
        content-align: center middle;
    }

    VerticalScroll {
        scrollbar-size: 0 0;
    }
    """

    def compose(self) -> ComposeResult:
        yield TypingConfigStrip()
        yield Pad(classes="cspan3")
        yield Pad()
        yield Ticker()
        yield Pad()
        yield Pad()
        with TypingScroll():
            yield Space()
        yield Pad()
        yield Pad(classes="cspan3")
        yield PaletteOptions()


class TypingSpace(DitherPassthrough, Widget):
    """
    Widget that holds the game sidebar and the typing area
    """

    DEFAULT_CSS = """
    TypingSpace {
        layout: horizontal;
        height: 100%;
        width: 100%;
    }
    """

    def update_run_visibility(self) -> None:
        hidden = config_parser.get("game_mode") != "run"
        self.query_one(GameSidebar).set_class(hidden, "hidden")

    def compose(self) -> ComposeResult:
        sidebar = GameSidebar()
        sidebar.set_class(config_parser.get("game_mode") != "run", "hidden")
        yield sidebar
        yield TypingArea()

    def on_mount(self) -> None:
        self.query_one(JokerRow).update_jokers(run_manager.state.jokers)
        self._pause_header_animation()

    def _pause_header_animation(self) -> None:
        try:
            from typatro.ui.widgets.label import Banner

            self.app.screen.query_one(Banner).set_animation_active(False)
        except Exception:
            pass

    def keypress(self, key: str):
        if key == "ctrl+s":
            return self.screen.post_message(SetScreen("settings"))

        if key == "ctrl+l":
            return self.app.push_screen("language")

        if key == "ctrl+t":
            return self.app.push_screen("theme")

        self.query_one(Space).keypress(key)


class TypingScreen(BaseWindow):
    """
    Screen Widget for typing area!
    """

    def compose(self) -> ComposeResult:
        yield TypingSpace()

    async def handle_key(self, event: events.Key):
        if not self.visible:
            return

        event.stop()
        key = event.character if event.is_printable and event.character else event.key
        self.query_one(TypingSpace).keypress(key)

    def on_show(self) -> None:
        self._set_banner_animation(False)

    def on_hide(self) -> None:
        self._set_banner_animation(True)

    def _set_banner_animation(self, active: bool) -> None:
        try:
            from typatro.ui.widgets.label import Banner

            self.app.screen.query_one(Banner).set_animation_active(active)
        except Exception:
            pass
