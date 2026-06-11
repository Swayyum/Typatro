"""Balatro-style round score panel with slot machine odometer animation."""

import colorsys
import math

from rich.console import RenderableType
from rich.style import Style
from rich.text import Text
from textual.widget import Widget

from typatro.src.balatro_experience import is_balatro_experience
from typatro.src.scoring import ScoreState, format_number
from typatro.src.slot_machine import Odometer, hsv_to_hex


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
        self._pulse_frame = 0

    def on_mount(self) -> None:
        self._roll_timer = self.set_interval(
            self.TICK_INTERVAL, self._roll_tick, pause=True
        )
        self.set_experience_active(is_balatro_experience())

    def set_experience_active(self, active: bool) -> None:
        """Pause odometer roll and score pulse outside Balatro run mode."""
        if active:
            return
        if self._roll_timer is not None:
            self._roll_timer.pause()
        self.remove_class("rolling")
        self._odometer.snap()
        self._display_score = int(self._odometer.value)
        self._pulse_frame = 0
        self.refresh()

    def _roll_tick(self) -> None:
        if not is_balatro_experience():
            return
        self._display_score = self._odometer.tick()
        self._pulse_frame += 1
        if self._odometer.done:
            self._roll_timer.pause()
            self.remove_class("rolling")
        self.refresh()

    def update_score(self, state: ScoreState) -> None:
        self._chips = state.chips
        self._mult = state.mult
        self._odometer.set_target(state.score)
        if not is_balatro_experience():
            self._odometer.snap()
            self._display_score = int(self._odometer.value)
            self.remove_class("rolling")
            self.refresh()
            return
        if self._odometer.done:
            self._display_score = int(self._odometer.value)
            self.remove_class("rolling")
            if self._roll_timer is not None and hasattr(self._roll_timer, "pause"):
                self._roll_timer.pause()
        else:
            gap = state.score - self._display_score
            if gap <= 8:
                # Per-keystroke updates stay in sync without waiting on the timer.
                for _ in range(64):
                    if self._odometer.done:
                        break
                    self._display_score = self._odometer.tick()
                    self._pulse_frame += 1
            else:
                self._display_score = self._odometer.tick()
                self._pulse_frame += 1
            if self._odometer.done:
                self.remove_class("rolling")
                if self._roll_timer is not None and hasattr(self._roll_timer, "pause"):
                    self._roll_timer.pause()
            elif self._roll_timer is not None and hasattr(self._roll_timer, "resume"):
                self.add_class("rolling")
                self._roll_timer.resume()
        self.refresh()

    def reset(self) -> None:
        self._chips = 0
        self._mult = 1.0
        self._odometer = Odometer()
        self._display_score = 0
        self.remove_class("rolling")
        if self._roll_timer is not None:
            self._roll_timer.pause()
        self.refresh()

    def _pulsed_score_style(self, base: Style) -> Style:
        """Shimmer the themed score color while the odometer rolls."""
        if (
            not is_balatro_experience()
            or self._odometer.done
            or base.color is None
            or base.color.triplet is None
        ):
            return base
        r, g, b = (channel / 255.0 for channel in base.color.triplet)
        hue, _, saturation = colorsys.rgb_to_hls(r, g, b)
        brightness = 0.7 + 0.3 * abs(math.sin(self._pulse_frame * 0.45))
        pulsed = hsv_to_hex(hue * 360.0, min(1.0, saturation), brightness)
        return Style.combine([base, Style(color=pulsed, bold=True)])

    def render(self) -> RenderableType:
        chips_style = self.get_component_rich_style("--chips")
        mult_style = self.get_component_rich_style("--mult")
        score_style = self._pulsed_score_style(
            self.get_component_rich_style("--score")
        )
        label_style = self.get_component_rich_style("--label")

        score_str = format_number(self._display_score)
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
