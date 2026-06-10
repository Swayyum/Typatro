"""Joker pick screen after beating a blind."""

from rich.console import RenderableType
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Static

from typatro.src.jokers import JokerDef, pick_random_jokers
from typatro.ui.events import JokerSelected


class JokerOption(Widget):
    """Selectable joker card in the pick screen."""

    DEFAULT_CSS = """
    JokerOption {
        width: 26;
        height: auto;
        padding: 1 2;
        margin: 0 1;
        content-align: center middle;
        text-align: center;
    }
    """

    def __init__(self, joker: JokerDef, index: int, **kwargs) -> None:
        super().__init__(**kwargs)
        self.joker = joker
        self.index = index

    def on_click(self) -> None:
        self.post_message(JokerSelected(self.joker))

    def render(self) -> RenderableType:
        text = Text()
        text.append(f"  {self.joker.icon}  \n", style="bold #eac058")
        text.append(f"{self.joker.name}\n", style="bold")
        text.append(f"{self.joker.description}", style="italic")
        return text


class JokerChoicePanel(Widget):
    """Centered modal panel for the joker pick screen."""

    DEFAULT_CSS = """
    JokerChoicePanel {
        width: auto;
        height: auto;
        padding: 2 3;
        align: center middle;
    }

    JokerChoicePanel > Vertical {
        width: auto;
        height: auto;
        align: center middle;
    }

    #joker-title {
        text-align: center;
        text-style: bold;
        height: auto;
        width: auto;
        margin-bottom: 1;
    }

    #joker-subtitle {
        text-align: center;
        height: auto;
        width: auto;
        margin-bottom: 2;
    }

    #joker-options {
        width: auto;
        height: auto;
        layout: horizontal;
        align: center middle;
    }
    """


class JokerChoiceScreen(Screen):
    """Pick 1 of 3 jokers after beating a blind."""

    DEFAULT_CSS = """
    JokerChoiceScreen {
        align: center middle;
    }
    """

    BINDINGS = [
        ("escape", "skip", "Skip"),
    ]

    def __init__(self, exclude_ids: list[str] | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.exclude_ids = exclude_ids or []
        self._choices = pick_random_jokers(3, self.exclude_ids)

    def compose(self) -> ComposeResult:
        with JokerChoicePanel():
            with Vertical():
                yield Static("Choose a Joker", id="joker-title")
                yield Static("Pick one to add to your run", id="joker-subtitle")
                with Horizontal(id="joker-options"):
                    for i, joker in enumerate(self._choices):
                        yield JokerOption(joker, i)

    def action_skip(self) -> None:
        self.dismiss(None)

    def on_joker_selected(self, event: JokerSelected) -> None:
        self.dismiss(event.joker)
