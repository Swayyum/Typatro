"""Joker list widget for the game sidebar."""

from rich.console import RenderableType
from rich.text import Text
from textual.widget import Widget

from typatro.src.jokers import MAX_JOKERS, JokerDef
from typatro.ui.widgets.balatro.joker_card_art import render_joker_line


class JokerRow(Widget):
    """Compact list of held jokers, one card stub per line."""

    DEFAULT_CSS = """
    JokerRow {
        width: 100%;
        height: auto;
        padding: 0 1;
    }
    """

    COMPONENT_CLASSES = {"--label", "--muted"}

    LINE_WIDTH = 28

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._jokers: list[JokerDef] = []

    def update_jokers(self, jokers: list[JokerDef]) -> None:
        self._jokers = jokers
        self.refresh()

    def reset(self) -> None:
        self._jokers = []
        self.refresh()

    def render(self) -> RenderableType:
        label_style = self.get_component_rich_style("--label")
        muted_style = self.get_component_rich_style("--muted")

        text = Text()
        text.append(f"JOKERS {len(self._jokers)}/{MAX_JOKERS}\n", style=label_style)

        if not self._jokers:
            text.append(" beat a blind to earn one", style=muted_style)
            return text

        for index, joker in enumerate(self._jokers):
            if index:
                text.append("\n")
            text.append_text(render_joker_line(joker, self.LINE_WIDTH))

        return text
