from rich.console import RenderableType
from rich.text import Text
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Digits, Static

from typatro.src.parser import data_parser
from typatro.src.scoring import ScoreState, format_number
from typatro.src import config_parser
from typatro.src.slot_machine import DigitSpin


class ValueLabel(Widget):
    """
    Label Widgets for values in result screen
    """

    DEFAULT_CSS = """
    ValueLabel {
        height: auto;
        width: auto;
    }
    """

    COMPONENT_CLASSES = {"--personal-best"}

    best = False

    def __init__(self, text: str, **kwargs) -> None:
        self.text = Text(text)
        super().__init__(**kwargs)

    def set_best(self, is_best: bool) -> None:
        self.best = is_best
        self.refresh()

    def render(self) -> RenderableType:
        style = self.get_component_rich_style("--personal-best")
        best_icon = Text(" 󱟜 " if self.best else "", style=style)
        return self.text + best_icon


class AutoVertical(Widget):
    DEFAULT_CSS = """
    AutoVertical {
        layout: vertical;
        margin: 1;
        height: auto;
        width: auto;
    }
    """


class Value(Digits, Static):
    """
    Result value in a large font, revealed with a slot machine digit spin:
    digits cycle randomly then lock in left to right.
    """

    DEFAULT_CSS = """
    Value {
        margin: 0 2;
        content-align: right middle;
        height: auto;
        width: auto;
    }
    """

    SPIN_INTERVAL = 0.05

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._spin: DigitSpin | None = None
        self._spin_timer = None

    def on_mount(self) -> None:
        self._spin_timer = self.set_interval(
            self.SPIN_INTERVAL, self._spin_tick, pause=True
        )

    def _spin_tick(self) -> None:
        if self._spin is None:
            return
        super().update(self._spin.tick())
        if self._spin.done:
            super().update(self._spin.target)
            self._spin = None
            self._spin_timer.pause()

    def update(self, value: str = "") -> None:
        """Reveal the value with a digit-spin animation when possible."""
        if self._spin_timer is None or not value.isdigit():
            super().update(value)
            return

        self._spin = DigitSpin(target=value)
        super().update("0" * len(value))
        self._spin_timer.resume()


class ValueContainer(Static):
    """
    Container widget that holds all the Values
    """

    DEFAULT_CSS = """
    ValueContainer {
        layout: horizontal;
        margin: 0 2;
        height: auto;
        width: 100%;
        align: center middle;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.wpm = Value()
        self.accuracy = Value()
        self.score = Value()

    def update_stats(self, stats, score_state: ScoreState | None = None) -> None:
        wpm_label = self.query_one("#wpm_label", expect_type=ValueLabel)
        wpm_label.set_best(data_parser.is_highest_wpm(stats.wpm))

        acc_label = self.query_one("#acc_label", expect_type=ValueLabel)
        acc_label.set_best(data_parser.is_highest_accuracy(stats.accuracy))

        self.wpm.update(str(stats.wpm))
        self.accuracy.update(str(stats.accuracy))

        score_container = self.query_one("#score_container", AutoVertical)
        if config_parser.get("game_mode") == "run" and score_state:
            score_container.display = True
            # Plain digits below the sci-notation threshold preserve the
            # digit-spin reveal; huge scores fall back to "1.234e13" style.
            self.score.update(format_number(score_state.score, sep=""))
        else:
            score_container.display = False

    def compose(self) -> ComposeResult:
        with AutoVertical():
            yield ValueLabel("WPM", id="wpm_label")
            yield self.wpm

        with AutoVertical():
            yield ValueLabel("ACC", id="acc_label")
            yield self.accuracy

        with AutoVertical(id="score_container"):
            yield ValueLabel("SCORE", id="score_label")
            yield self.score
