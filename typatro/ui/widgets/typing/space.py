from bisect import bisect_right
from typing import List
from rich.console import RenderableType
from rich.style import Style
from rich.text import Span, Text
from textual.widget import Widget
from textual.widgets import Static
from typatro.src import master_generator, Tracker, Cursor, ScoringEngine, run_manager, config_parser
from typatro.src.buddy import Buddy
from typatro.ui.events import ShowResults
from typatro.ui.widgets.typing.ticker import Ticker


def _notify_typing_activity(space: "Space") -> None:
    try:
        from typatro.ui.widgets.balatro import DitherBackground

        space.app.query_one(DitherBackground).on_typing_activity()
    except Exception:
        pass


def _get_score_panel(space: "Space"):
    try:
        from typatro.ui.widgets.balatro import ScorePanel

        return space.screen.query_one(ScorePanel)
    except Exception:
        return None


def _get_blind_card(space: "Space"):
    try:
        from typatro.ui.widgets.balatro import BlindCard

        return space.screen.query_one(BlindCard)
    except Exception:
        return None


def _is_run_mode() -> bool:
    return config_parser.get("game_mode") == "run"


def caret(func):
    def wrapper(space: "Space") -> Text:
        renderable: Text = func(space).copy()
        setting = config_parser.get("caret_style")
        pos = space.tracker.cursor_pos

        if setting == "off" or pos == len(space.paragraph.plain):
            return renderable

        if setting == "underline":
            rich_style = "--caret-underline"
        else:
            rich_style = "--caret-block"

        style = space.get_component_rich_style(rich_style)
        renderable.spans.append(Span(pos, pos + 1, style))

        return renderable

    return wrapper


def tab_reset(func):
    def wrapper(space: "Space", key: str) -> None:
        if key == "tab" and config_parser.get("tab_reset"):
            return space.restart()

        return func(space, key)

    return wrapper


def toggle_settings(func):
    def wrapper(space: "Space", key: str) -> None:
        config_changed = False

        if key == "ctrl+n":
            config_parser.toggle_numbers()
            config_changed = True

        elif key == "ctrl+p":
            config_parser.toggle_punctuations()
            config_changed = True

        if config_changed:
            for i in space.screen.query("Switchable"):
                i.refresh()

            return space.restart()

        return func(space, key)

    return wrapper


def cursor_buddy(func):
    def wrapper(space: "Space") -> RenderableType:
        wpm = config_parser.get("cursor_buddy_speed")
        res = func(space)

        if not wpm or not space.tracker.stats.start_time:
            return res

        elapsed = space.tracker.stats.elapsed_time
        letters_typed = Buddy.get_letters_typed(elapsed, wpm, 5)
        letters_typed = min(letters_typed, len(space.paragraph.plain) - 1)

        res_copy = res.copy()
        style = space.get_component_rich_style("--cursor-buddy")
        res_copy.spans.append(Span(letters_typed, letters_typed + 1, style))
        return res_copy

    return wrapper


def blind_mode(func):
    def wrapper(space: "Space", *args, **kwargs) -> Style:
        if config_parser.get("blind_mode") == "on":
            return space.get_component_rich_style("--blind-match")

        return func(space, *args, **kwargs)

    return wrapper


def incorrect_spaces(func):
    INCORRECT_SPACE_CHARACTER = "░"

    def wrapper(space: "Space") -> RenderableType:
        text: Text = func(space)
        incorrect_style = space.get_match_style(False)

        plain_text = text.plain

        for span in text.spans:
            if span.style == incorrect_style and plain_text[span.start] == " ":
                plain_text = (
                    plain_text[: span.start]
                    + INCORRECT_SPACE_CHARACTER
                    + plain_text[span.end :]
                )

        text.plain = plain_text
        return text

    return wrapper


class Space(Static):
    """
    Space Widget to handle keypress and display typing text
    """

    COMPONENT_CLASSES = {
        "--cursor-buddy",
        "--correct-match",
        "--incorrect-match",
        "--blind-match",
        "--caret-underline",
        "--caret-block",
    }

    def __init__(self) -> None:
        super().__init__()
        self.current_key = None
        self.scoring = ScoringEngine()
        self.target_score = 0
        self._styled_spans: List[Span] = []
        self.reset()
        self.check_timer = self.set_interval(1, self.check_restrictions, pause=True)
        if config_parser.get("cursor_buddy_speed"):
            self.set_interval(0.2, self.refresh)

    # ---------------- UTILS -----------------

    def cursor_row(self, cursor_pos: int) -> int:
        return bisect_right(self.newlines, cursor_pos)

    def cursor_span(self, pos: int) -> Span:
        return Span(pos, pos + 1, "reverse white")

    # ----------------- RENDER ------------------
    def on_show(self) -> None:
        self.reset_newlines()

    def _wrap_width(self) -> int:
        """Paragraph wrap width in terminal cells."""
        return max(1, self.size.width)

    def reset_newlines(self) -> None:
        self.newlines = master_generator.get_newlines(
            self.paragraph.plain,
            self._wrap_width(),
        )

    def restart(self, force: bool = False) -> None:
        if force:
            generated = self.paragraph.plain
            self.paragraph = Text(generated)
            self.reset_components()
        else:
            self.reset()

    def check_restrictions(self) -> None:
        if not self.tracker.stats.start_time or self.tracker.stats.elapsed_time < 1:
            return

        if min_speed := config_parser.get("min_speed"):
            wpm = self.tracker.stats.wpm
            if wpm < min_speed:
                return self.finish_typing()

        if min_accuracy := config_parser.get("min_accuracy"):
            accuracy = self.tracker.stats.accuracy
            if accuracy < min_accuracy:
                return self.finish_typing()

        if min_burst := config_parser.get("min_burst"):
            burst = self.tracker.stats.last_word_wpm
            if burst < min_burst:
                return self.finish_typing()

    def finish_typing(self, fail: bool = True) -> None:
        score_state = None
        blind_beaten = False

        if _is_run_mode():
            score_state = self.scoring.finalize(self.tracker.stats)
            panel = _get_score_panel(self)
            if panel:
                panel.update_score(score_state)

            if not fail and score_state.score >= self.target_score:
                blind_beaten = True
                run_manager.state.advance_blind(score_state.score)
                run_manager.save()

        self.screen.post_message(
            ShowResults(
                self.tracker.stats,
                fail,
                score_state=score_state,
                target_score=self.target_score,
                blind_beaten=blind_beaten,
            )
        )

    def reset(self) -> None:
        mode = config_parser.get("mode")
        if mode == "words":
            word_count = config_parser.get(f"{mode}_count")
        else:
            minutes = config_parser.get(f"{mode}_count") / 60
            word_count = round(600 * minutes)

        language = config_parser.get("language")

        generated = master_generator.generate(
            language,
            word_count,
        )

        self.paragraph = Text(generated)
        self.reset_components()

    def _update_run_visibility(self) -> None:
        try:
            from typatro.src.balatro_experience import sync_balatro_experience
            from typatro.ui.screens.typing import TypingSpace

            self.screen.query_one(TypingSpace).update_run_visibility()
            sync_balatro_experience(self.app)
        except Exception:
            pass

    def reset_components(self) -> None:
        self.tracker = Tracker(self.paragraph.plain)
        self._update_run_visibility()

        if _is_run_mode():
            run_manager.state.apply_blind_debuffs()
            self.target_score = run_manager.state.target_score()
            self.scoring.reset(jokers=run_manager.state.jokers)

            blind_card = _get_blind_card(self)
            if blind_card:
                blind_card.update_blind(
                    run_manager.state.current_blind,
                    self.target_score,
                    run_manager.state.ante,
                )

            panel = _get_score_panel(self)
            if panel:
                panel.reset()
        else:
            self.target_score = 0
            self.scoring.reset()

        self.cursor = 0
        self._styled_spans = []

        if self.size.width:
            self.reset_newlines()
            self.screen.query_one(Ticker).reset()

        self.refresh(layout=True)

    @cursor_buddy
    @caret
    @incorrect_spaces
    def render(self) -> RenderableType:
        self.paragraph.spans = self._styled_spans
        return self.paragraph

    @blind_mode
    def get_match_style(self, correct: bool) -> Style:
        rich_style = "correct" if correct else "incorrect"
        style = self.get_component_rich_style(f"--{rich_style}-match")
        return style

    def update_colors(self, cursor: Cursor) -> None:
        old = cursor.old
        new = cursor.new
        correct = cursor.correct

        if new < old:
            self._styled_spans = self._styled_spans[:new]
            return

        diff = new - old
        if diff > 1:
            blank = self.get_match_style(True)
            for pos in range(old, new - 1):
                self._styled_spans.append(Span(pos, pos + 1, blank))

        if diff >= 1:
            self._styled_spans.append(
                Span(new - 1, new, self.get_match_style(correct))
            )

    # ---------------- KEYPRESS -----------------

    @toggle_settings
    @tab_reset
    def keypress(self, key: str) -> None:
        if key == "escape":
            return self.reset()

        cursor = self.tracker.keypress(key)
        if not cursor:
            return

        current_row = self.cursor_row(cursor.old)
        new_row = self.cursor_row(cursor.new)

        if current_row != new_row and isinstance(self.parent, Widget):
            if new_row > current_row:
                if current_row:
                    self.parent.scroll_down()
            else:
                if current_row != len(self.newlines) - 1:
                    self.parent.scroll_up()

        self.update_colors(cursor)
        _notify_typing_activity(self)

        if _is_run_mode():
            state = self.scoring.on_keystroke(cursor, self.tracker.stats)
            panel = _get_score_panel(self)
            if panel:
                panel.update_score(state)

        if cursor.new == len(self.paragraph.plain):
            return self.finish_typing(fail=False)

        self.check_timer.resume()
        self.screen.query_one(Ticker).update_check.resume()
        self.refresh(layout=False)
