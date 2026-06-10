"""Balatro-style round score panel with slot machine odometer animation."""

from rich.console import RenderableType
from rich.text import Text
from textual.widget import Widget

from typatro.src.scoring import ScoreState
from typatro.src.slot_machine import Odometer


class ScorePanel(Widget):
    """Vertical score card: round score on top, Chips x Mult below.

    The score rolls toward its target like a slot machine tally instead of
    jumping, driven by an interval timer.
    """

    DEFAULT_CSS = """
    ScorePanel {
        width: 100%;
        height: auto;
        padding: 0 1;
    }
    """

    COMPONENT_CLASSES = {"--chips", "--mult", "--score", "--label"}

    TICK_INTERVAL = 0.04

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._chips = 0
        self._mult = 1.0
        self._odometer = Odometer()
        self._display_score = 0
        self._roll_timer = None

    def on_mount(self) -> None:
        self._roll_timer = self.set_interval(
            self.TICK_INTERVAL, self._roll_tick, pause=True
        )

    def _roll_tick(self) -> None:
        self._display_score = self._odometer.tick()
        if self._odometer.done:
            self._roll_timer.pause()
        self.refresh()

    def update_score(self, state: ScoreState) -> None:
        self._chips = state.chips
        self._mult = state.mult
        self._odometer.set_target(state.score)
        if self._roll_timer is not None and not self._odometer.done:
            self._roll_timer.resume()
        elif self._roll_timer is None:
            self._odometer.snap()
            self._display_score = int(self._odometer.value)
        self.refresh()

    def reset(self) -> None:
        self._chips = 0
        self._mult = 1.0
        self._odometer = Odometer()
        self._display_score = 0
        self.refresh()

    def render(self) -> RenderableType:
        chips_style = self.get_component_rich_style("--chips")
        mult_style = self.get_component_rich_style("--mult")
        score_style = self.get_component_rich_style("--score")
        label_style = self.get_component_rich_style("--label")

        score_str = f"{self._display_score:,}"
        chips_str = f" {self._chips} "
        mult_str = f" {self._mult:.1f} "

        text = Text()
        text.append("ROUND SCORE\n", style=label_style)
        text.append(f"  {score_str}\n", style=score_style)
        text.append("\n")
        text.append(chips_str, style=chips_style)
        text.append(" x ", style=label_style)
        text.append(mult_str, style=mult_style)
        return text
