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
from typatro.ui.widgets.balatro import ScorePanel, BlindCard, JokerRow
from textual.containers import VerticalScroll
from typatro.ui.events import SetScreen
from typatro.src import run_manager, config_parser


class TypingScroll(VerticalScroll, can_focus=False):
    pass


class Pad(Widget):
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

    DEFAULT_CSS = """
    GameSidebar {
        layout: vertical;
        width: 34;
        height: 100%;
        padding: 1 1;
    }

    GameSidebar.hidden {
        display: none;
    }

    GameSidebar > BlindCard {
        margin-bottom: 1;
    }

    GameSidebar > ScorePanel {
        margin-bottom: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield BlindCard()
        yield ScorePanel()
        yield JokerRow()


class TypingArea(Widget):
    """Main typing column: config strip, ticker, paragraph."""

    DEFAULT_CSS = """
    TypingArea {
        layout: grid;
        grid-size: 3 6;
        grid-columns: 1fr 4fr 1fr;
        grid-rows: 1 1fr 1 3 1fr 1;
        height: 100%;
        width: 1fr;
        margin: 1;
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


class TypingSpace(Widget):
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
