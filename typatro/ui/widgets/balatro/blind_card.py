"""Blind card widget styled like Balatro's blind panel."""

from rich.console import RenderableType
from rich.text import Text
from textual.widget import Widget

from typatro.src.blind import BlindDef, BlindType
from typatro.src.parser import config_parser
from typatro.src.run_state import run_manager

BLIND_GLYPHS = {
    BlindType.SMALL: "( S )",
    BlindType.BIG: "( B )",
    BlindType.BOSS: "(BOSS)",
}


class BlindCard(Widget):
    """Card showing ante, blind name, target score, and reward."""

    DEFAULT_CSS = """
    BlindCard {
        width: 100%;
        height: auto;
        padding: 0 1;
    }
    """

    COMPONENT_CLASSES = {"--blind-name", "--target", "--reward", "--ante"}

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._blind: BlindDef | None = None
        self._target = 0
        self._ante = 1

    def on_mount(self) -> None:
        if config_parser.get("game_mode") == "run":
            self.update_blind(
                run_manager.state.current_blind,
                run_manager.state.target_score(),
                run_manager.state.ante,
            )

    def update_blind(self, blind: BlindDef, target: int, ante: int) -> None:
        self._blind = blind
        self._target = target
        self._ante = ante
        self.refresh()

    def reset(self) -> None:
        self._blind = None
        self._target = 0
        self.refresh()

    def render(self) -> RenderableType:
        name_style = self.get_component_rich_style("--blind-name")
        target_style = self.get_component_rich_style("--target")
        reward_style = self.get_component_rich_style("--reward")
        ante_style = self.get_component_rich_style("--ante")

        if not self._blind:
            return Text("FREE PLAY", style=name_style)

        blind = self._blind
        glyph = BLIND_GLYPHS.get(blind.blind_type, "( ? )")

        text = Text()
        text.append(f"ANTE {self._ante}\n", style=ante_style)
        text.append(f"{glyph} {blind.name.upper()}\n", style=name_style)
        if blind.boss:
            text.append(
                f"{blind.boss.value.replace('_', ' ').title()}\n", style=reward_style
            )
        text.append("Score at least\n", style=reward_style)
        text.append(f"  {self._target:,}\n", style=target_style)
        text.append(f"Reward: {blind.reward}", style=reward_style)
        return text
