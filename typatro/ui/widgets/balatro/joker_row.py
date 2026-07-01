"""Joker list widget for the game sidebar."""

from rich.console import RenderableType
from rich.text import Text
from textual.widget import Widget

from typatro.src.jokers import MAX_JOKERS, JokerDef
from typatro.ui.sidebar_layout import SIDEBAR_INNER_WIDTH
from typatro.ui.widgets.balatro.joker_card_art import render_joker_sidebar_entry


class JokerRow(Widget):
    """Held jokers in the run sidebar — one readable block per joker."""

    DEFAULT_CSS = """
    JokerRow {
        width: 100%;
        height: auto;
        padding: 0 1;
    }
    """

    COMPONENT_CLASSES = {
        "--label",
        "--muted",
        "--joker-icon",
        "--joker-name",
        "--joker-mult",
        "--joker-chips",
    }

    LINE_WIDTH = SIDEBAR_INNER_WIDTH

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
        icon_style = self.get_component_rich_style("--joker-icon")
        name_style = self.get_component_rich_style("--joker-name")
        mult_style = self.get_component_rich_style("--joker-mult")
        chips_style = self.get_component_rich_style("--joker-chips")

        text = Text()
        text.append(f"JOKERS {len(self._jokers)}/{MAX_JOKERS}\n", style=label_style)

        if not self._jokers:
            text.append(" beat a blind to earn one", style=muted_style)
            return text

        for index, joker in enumerate(self._jokers):
            if index:
                text.append("\n")
            text.append_text(
                render_joker_sidebar_entry(
                    joker,
                    self.LINE_WIDTH,
                    icon_style=icon_style,
                    name_style=name_style,
                    mult_style=mult_style,
                    chips_style=chips_style,
                    muted_style=muted_style,
                    slot=index + 1,
                )
            )

        return text
