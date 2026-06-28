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
from typatro.ui.widgets.balatro.dither import DitherBackground
from typatro.ui.widgets.balatro.joker_card_art import (
    CARD_HEIGHT as JOKER_CARD_HEIGHT,
    CARD_WIDTH as JOKER_CARD_WIDTH,
    render_joker_card,
)


class JokerOptionsRow(Horizontal):
    """Horizontal row of joker cards — must not shrink or cards stack vertically."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.shrink = False


class JokerOption(Widget):
    """Selectable joker card in the pick screen."""

    DEFAULT_CSS = """
    JokerOption {
        width: 28;
        height: 11;
        min-width: 28;
        min-height: 11;
        margin: 0 1;
        content-align: center middle;
        background: #f6f1e3;
    }
    """

    CARD_WIDTH = JOKER_CARD_WIDTH
    CARD_HEIGHT = JOKER_CARD_HEIGHT

    def __init__(self, joker: JokerDef, index: int, **kwargs) -> None:
        super().__init__(**kwargs)
        self.joker = joker
        self.index = index

    def on_click(self) -> None:
        self.post_message(JokerSelected(self.joker))

    def render(self) -> RenderableType:
        phase = 0.0
        screen = self.screen
        if isinstance(screen, JokerChoiceScreen):
            phase = getattr(screen, "_art_phase", 0.0)
        return render_joker_card(
            self.joker,
            self.CARD_WIDTH,
            index_label=f"[ {self.index + 1} ]",
            phase=phase,
            screen_x=self.region.x,
            screen_y=self.region.y,
        )


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
        min-width: 90;
        layout: horizontal;
        align: center middle;
        content-align: center middle;
    }
    """


class JokerChoiceScreen(Screen):
    """Pick 1 of 3 jokers after beating a blind."""

    DEFAULT_CSS = """
    JokerChoiceScreen {
        align: center middle;
        layers: backdrop panel;
    }

    JokerChoiceScreen > DitherBackground {
        layer: backdrop;
        width: 100%;
        height: 100%;
    }

    JokerChoiceScreen > JokerChoicePanel {
        layer: panel;
    }
    """

    BINDINGS = [
        ("1", "pick_one", "Pick 1"),
        ("2", "pick_two", "Pick 2"),
        ("3", "pick_three", "Pick 3"),
        ("escape", "skip", "Skip"),
    ]

    def __init__(self, exclude_ids: list[str] | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.exclude_ids = exclude_ids or []
        self._choices = pick_random_jokers(3, self.exclude_ids)

    def compose(self) -> ComposeResult:
        yield DitherBackground()
        with JokerChoicePanel():
            with Vertical():
                yield Static("Choose a Joker", id="joker-title")
                yield Static(
                    "Pick one · press 1–3 · click · Esc to skip",
                    id="joker-subtitle",
                )
                with JokerOptionsRow(id="joker-options"):
                    for i, joker in enumerate(self._choices):
                        yield JokerOption(joker, i)

    def on_mount(self) -> None:
        self._art_phase = 0.0

    def _pick(self, index: int) -> None:
        if 0 <= index < len(self._choices):
            self.dismiss(self._choices[index])

    def action_pick_one(self) -> None:
        self._pick(0)

    def action_pick_two(self) -> None:
        self._pick(1)

    def action_pick_three(self) -> None:
        self._pick(2)

    def action_skip(self) -> None:
        self.dismiss(None)

    def on_joker_selected(self, event: JokerSelected) -> None:
        self.dismiss(event.joker)
