"""Joker list widget for the game sidebar."""

from rich.console import RenderableType
from rich.text import Text
from textual.widget import Widget

from typatro.src.jokers import MAX_JOKERS, JokerDef


class JokerRow(Widget):
    """Vertical list of held jokers, card-stub style."""

    DEFAULT_CSS = """
    JokerRow {
        width: 100%;
        height: auto;
        padding: 0 1;
    }
    """

    COMPONENT_CLASSES = {"--joker-icon", "--joker-name", "--joker-desc", "--label"}

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
        icon_style = self.get_component_rich_style("--joker-icon")
        name_style = self.get_component_rich_style("--joker-name")
        desc_style = self.get_component_rich_style("--joker-desc")
        label_style = self.get_component_rich_style("--label")

        text = Text()
        text.append(f"JOKERS {len(self._jokers)}/{MAX_JOKERS}\n", style=label_style)

        if not self._jokers:
            text.append("  (beat a blind to earn one)", style=desc_style)
            return text

        for joker in self._jokers:
            text.append(f" {joker.icon} ", style=icon_style)
            text.append(f"{joker.name}\n", style=name_style)
            text.append(f"    {joker.description}\n", style=desc_style)

        return text
