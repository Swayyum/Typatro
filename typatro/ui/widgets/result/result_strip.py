from rich.console import RenderableType
from textual.app import ComposeResult
from textual.widgets import Label, Static
from typatro.ui.events import SetScreen
from typatro.ui.widgets import Space
from typatro.src import config_parser, run_manager


class ResultStripItem(Label):
    """
    A strip widget item containg action after typing is finished
    """

    DEFAULT_CSS = """
    ResultStripItem {
        padding: 0 3;
    }
    """

    icon: str
    help: str

    def on_mount(self) -> None:
        self.tooltip = self.help

    def render(self) -> RenderableType:
        return self.icon


class NextTest(ResultStripItem):
    icon = "Next"
    help = "Next test"

    def on_click(self, _) -> None:
        main = self.app.get_screen("main")
        if getattr(main, "_pending_joker_pick", False):
            main._pending_joker_pick = False
            main.offer_joker_pick()
        self.screen.query_one(Space).reset()
        self.post_message(SetScreen("typing"))


class RepeatTest(ResultStripItem):
    icon = "Retry"
    help = "Repeat test"

    def on_click(self, _) -> None:
        main = self.app.get_screen("main")
        main._pending_joker_pick = False
        self.screen.query_one(Space).restart(force=True)
        self.post_message(SetScreen("typing"))


class ResultStrip(Static):
    """
    Strip widget that contain all the available actions on result screen
    """

    DEFAULT_CSS = """
    ResultStrip {
        layout: horizontal;
        align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        yield NextTest()
        yield RepeatTest()
