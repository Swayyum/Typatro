"""Blind card widget styled like Balatro's blind panel."""

from rich.console import RenderableType
from rich.text import Text
from textual.widget import Widget

from typatro.src.balatro_experience import is_balatro_experience
from typatro.src.blind import BlindDef, BlindType
from typatro.src.run_state import run_manager
from typatro.src.scoring import format_number

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
    PULSE_SECONDS = 0.55

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._blind: BlindDef | None = None
        self._target = 0
        self._ante = 1
        self._pulse_timer = None

    def on_mount(self) -> None:
        if is_balatro_experience():
            self.update_blind(
                run_manager.state.current_blind,
                run_manager.state.target_score(),
                run_manager.state.ante,
            )

    def set_experience_active(self, active: bool) -> None:
        """Cancel blind-card pulse animation outside Balatro run mode."""
        if active:
            return
        if self._pulse_timer is not None:
            self._pulse_timer.stop()
            self._pulse_timer = None
        self.remove_class("pulse")

    def update_blind(self, blind: BlindDef, target: int, ante: int) -> None:
        self._blind = blind
        self._target = target
        self._ante = ante
        if is_balatro_experience():
            self._pulse()
        self.refresh()

    def _pulse(self) -> None:
        if self._pulse_timer is not None:
            self._pulse_timer.stop()
        self.add_class("pulse")
        self._pulse_timer = self.set_timer(
            self.PULSE_SECONDS, self._end_pulse, name="blind-pulse"
        )

    def _end_pulse(self) -> None:
        self.remove_class("pulse")
        self._pulse_timer = None

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
        text.append(f"  {format_number(self._target)}\n", style=target_style)
        text.append(f"Reward: {blind.reward}", style=reward_style)
        return text
