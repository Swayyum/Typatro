from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static
from typatro.src.stats_tracker import StatsTracker
from typatro.src.scoring import ScoreState
from typatro.ui.widgets import BaseWindow
from typatro.ui.widgets.typing.space import Space
from typatro.ui.widgets.result import ValueContainer, Value, ResultStrip
from typatro.ui.widgets.typing.ticker import Ticker
from typatro.src import config_parser


class AutoVertical(Static):
    DEFAULT_CSS = """
    AutoVertical {
        margin: 1;
        height: auto;
        width: auto;
        background: red;
    }
    """


class AutoHorizontal(Static):
    DEFAULT_CSS = """
    AutoVertical {
        layout: horizontal;
        margin: 1;
        height: auto;
        width: auto;
    }
    """


class ResultScreen(BaseWindow):
    """
    This screen will show the result of the typing test.
    E.g. Typing Chart, Accuracy, WPM etc.
    """

    DEFAULT_CSS = """
    ResultScreen {
        layout: grid;
        grid-size: 1 5;
        grid-rows: auto 1fr auto 1 1fr;
        align: center middle;
    }

    #blind-result {
        text-align: center;
        height: auto;
        width: 100%;
        text-style: bold;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.wpm = Value()
        self.accuracy = Value()
        self._blind_beaten = False
        self._score_state: ScoreState | None = None
        self._target_score = 0

    def compose(self) -> ComposeResult:
        yield Static("", id="blind-result")
        yield Container()
        yield ValueContainer()
        yield ResultStrip()
        yield Container()

    def set_results(
        self,
        stats: StatsTracker,
        score_state: ScoreState | None = None,
        target_score: int = 0,
        blind_beaten: bool = False,
        failed: bool = False,
    ) -> None:
        self.stats = stats
        self._score_state = score_state
        self._target_score = target_score
        self._blind_beaten = blind_beaten
        self.query_one(ValueContainer).update_stats(stats, score_state)

        blind_label = self.query_one("#blind-result", Static)
        if config_parser.get("game_mode") == "run" and score_state:
            if failed:
                blind_label.update("Run failed — restrictions not met")
                blind_label.set_class(True, "lost")
                blind_label.set_class(False, "beaten")
            elif blind_beaten:
                blind_label.update(
                    f"Blind beaten! Score: {score_state.score} / {target_score}"
                )
                blind_label.set_class(True, "beaten")
                blind_label.set_class(False, "lost")
            else:
                blind_label.update(
                    f"Blind lost. Score: {score_state.score} / {target_score}"
                )
                blind_label.set_class(True, "lost")
                blind_label.set_class(False, "beaten")
        else:
            blind_label.update("")

    def on_hide(self) -> None:
        space = self.screen.query_one(Space)
        if space.paragraph.spans:
            self.screen.query_one(Ticker).reset()
            space.restart()
