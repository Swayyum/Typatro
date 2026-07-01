from bisect import bisect_right
from typing import List, Optional, Set

from rich.console import RenderableType
from rich.style import Style
from rich.text import Span, Text
from textual.widget import Widget
from textual.widgets import Static

from typatro.src import (
    Cursor,
    ScoringEngine,
    Tracker,
    config_parser,
    master_generator,
    run_manager,
)
from typatro.src.buddy import Buddy
from typatro.ui.events import ShowResults
from typatro.ui.widgets.typing.ticker import Ticker

_INCORRECT_SPACE_CHARACTER = "░"


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
        self._incorrect_space_positions: Set[int] = set()
        self._style_correct: Style = Style()
        self._style_incorrect: Style = Style()
        self._caret_style: Optional[Style] = None
        self._buddy_style: Style = Style()
        self._buddy_wpm = 0
        self._styles_initialized = False
        self._dither_bg = None
        self._score_panel = None
        self._ticker: Optional[Ticker] = None
        self.reset()
        self.check_timer = self.set_interval(1, self.check_restrictions, pause=True)

    def on_mount(self) -> None:
        self._cache_styles()
        try:
            from typatro.ui.widgets.balatro import DitherBackground

            self._dither_bg = self.app.query_one(DitherBackground)
        except Exception:
            self._dither_bg = None
        self._score_panel = _get_score_panel(self)
        try:
            self._ticker = self.screen.query_one(Ticker)
        except Exception:
            self._ticker = None
        if self._buddy_wpm:
            self.set_interval(0.5, self._refresh_cursor_buddy)

    def _refresh_cursor_buddy(self) -> None:
        if self._buddy_wpm:
            self.refresh(layout=False)

    def _cache_styles(self) -> None:
        if not self.is_mounted:
            return
        blind = config_parser.get("blind_mode") == "on"
        if blind:
            blind_style = self.get_component_rich_style("--blind-match")
            self._style_correct = blind_style
            self._style_incorrect = blind_style
        else:
            self._style_correct = self.get_component_rich_style("--correct-match")
            self._style_incorrect = self.get_component_rich_style("--incorrect-match")

        setting = config_parser.get("caret_style")
        if setting == "underline":
            self._caret_style = self.get_component_rich_style("--caret-underline")
        elif setting == "off":
            self._caret_style = None
        else:
            self._caret_style = self.get_component_rich_style("--caret-block")

        self._buddy_style = self.get_component_rich_style("--cursor-buddy")
        self._buddy_wpm = config_parser.get("cursor_buddy_speed")
        self._styles_initialized = True

    def _ensure_styles(self) -> None:
        if self.is_mounted and not self._styles_initialized:
            self._cache_styles()

    # ---------------- UTILS -----------------

    def cursor_row(self, cursor_pos: int) -> int:
        return bisect_right(self.newlines, cursor_pos)

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
            panel = self._score_panel or _get_score_panel(self)
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

            panel = self._score_panel or _get_score_panel(self)
            if panel:
                panel.reset()
        else:
            self.target_score = 0
            self.scoring.reset()

        self.cursor = 0
        self._styled_spans = []
        self._incorrect_space_positions = set()
        self._styles_initialized = False

        if self.size.width:
            self.reset_newlines()
            ticker = self._ticker or self.screen.query_one(Ticker)
            ticker.reset()

        self.refresh(layout=True)

    def _overlay_spans(self) -> List[Span]:
        extra: List[Span] = []
        pos = self.tracker.cursor_pos
        plain_len = len(self.paragraph.plain)

        if self._caret_style is not None and pos < plain_len:
            extra.append(Span(pos, pos + 1, self._caret_style))

        if self._buddy_wpm and self.tracker.stats.start_time:
            elapsed = self.tracker.stats.elapsed_time
            letters = min(Buddy.get_letters_typed(elapsed, self._buddy_wpm, 5), plain_len - 1)
            extra.append(Span(letters, letters + 1, self._buddy_style))

        return extra

    def render(self) -> RenderableType:
        self._ensure_styles()
        overlay = self._overlay_spans()
        spans: List[Span] = (
            self._styled_spans + overlay if overlay else self._styled_spans
        )

        if not self._incorrect_space_positions:
            self.paragraph.spans = spans
            return self.paragraph

        buf = list(self.paragraph.plain)
        for index in self._incorrect_space_positions:
            buf[index] = _INCORRECT_SPACE_CHARACTER
        text = Text("".join(buf))
        text.spans = spans
        return text

    def _truncate_styles(self, pos: int) -> None:
        trimmed: List[Span] = []
        for span in self._styled_spans:
            if span.start >= pos:
                break
            if span.end <= pos:
                trimmed.append(span)
            else:
                trimmed.append(Span(span.start, pos, span.style))
                break
        self._styled_spans = trimmed
        if self._incorrect_space_positions:
            self._incorrect_space_positions = {
                index for index in self._incorrect_space_positions if index < pos
            }

    def _append_styled_span(self, start: int, end: int, style: Style) -> None:
        if end <= start:
            return
        if self._styled_spans:
            last = self._styled_spans[-1]
            if last.style == style and last.end == start:
                self._styled_spans[-1] = Span(last.start, end, style)
                return
        self._styled_spans.append(Span(start, end, style))

    def update_colors(self, cursor: Cursor) -> None:
        old = cursor.old
        new = cursor.new
        correct = cursor.correct

        if new < old:
            self._truncate_styles(new)
            return

        style = self._style_correct if correct else self._style_incorrect
        if new - old > 1:
            for pos in range(old, new - 1):
                self._append_styled_span(pos, pos + 1, self._style_correct)

        if new > old:
            self._append_styled_span(new - 1, new, style)
            if not correct and self.paragraph.plain[new - 1] == " ":
                self._incorrect_space_positions.add(new - 1)

    def _notify_typing_activity(self) -> None:
        if self._dither_bg is None:
            try:
                from typatro.ui.widgets.balatro import DitherBackground

                self._dither_bg = self.app.query_one(DitherBackground)
            except Exception:
                return
        self._dither_bg.on_typing_activity()

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
        self._notify_typing_activity()

        if _is_run_mode():
            state = self.scoring.on_keystroke(cursor, self.tracker.stats)
            panel = self._score_panel or _get_score_panel(self)
            if panel:
                panel.push_score(state)

        if cursor.new == len(self.paragraph.plain):
            return self.finish_typing(fail=False)

        self.check_timer.resume()
        ticker = self._ticker
        if ticker is not None:
            ticker.update_check.resume()

        self.refresh(layout=False)
