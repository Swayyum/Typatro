from rich.console import RenderableType
from rich.text import Text
from textual.app import ComposeResult
from textual.widget import Widget
from typatro.ui.widgets import BaseWindow

DESCRIPTION = """
Typatro is a slot-machine typing roguelike for your terminal.

Type fast, build Chips × Mult, beat Blinds, collect Jokers, and climb Antes —
all wrapped in a casino-felt TUI with reel-spin animations.

Run mode, classic practice mode, and a large theme library are included.

Thanks for checking out this project!
"""

STAR = """
[@click=app.star]Star this project on GitHub![/]
"""

OUTRO = """
Made with ❤️  by Swayyum
"""


class Section(Widget):
    """
    Section Widget for each section of About Menu
    """

    DEFAULT_CSS = """
    Section {
        height: auto;
        content-align: center middle;
    }
    """

    def __init__(self, renderable: str) -> None:
        super().__init__()
        self.renderable = renderable

    def render(self) -> RenderableType:
        return Text.from_markup(self.renderable)


class AboutDescription(Section):
    def __init__(self) -> None:
        super().__init__(DESCRIPTION)


class Star(Section):
    def __init__(self) -> None:
        super().__init__(STAR)


class AboutOutro(Section):
    DEFAULT_CSS = """
    AboutOutro {
        content-align: center bottom;
        height: 100%;
    }
    """

    def __init__(self) -> None:
        super().__init__(OUTRO)


class AboutScreen(BaseWindow):
    """
    About screen to show info about the project
    """

    DEFAULT_CSS = """
    AboutScreen {
        layout: grid;
        grid-size: 1 3;
        grid-rows: auto auto 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        yield AboutDescription()
        yield Star()
        yield AboutOutro()
