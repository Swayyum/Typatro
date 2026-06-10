"""Chips x Mult scoring engine for Balatro run mode."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from typatro.src.jokers import JokerContext, JokerDef, apply_joker_effects
from typatro.src.stats_tracker import Match, StatsTracker
from typatro.src.tracker import Cursor


@dataclass
class ScoreState:
    chips: int = 0
    base_mult: float = 1.0
    bonus_mult: float = 0.0
    streak: int = 0
    prev_word_count: int = 0

    @property
    def mult(self) -> float:
        return max(1.0, self.base_mult + self.bonus_mult)

    @property
    def score(self) -> int:
        return int(self.chips * self.mult)


class ScoringEngine:
    """Tracks Chips x Mult score during a typing test."""

    CHIPS_PER_CHAR = 1
    WORD_BONUS = 10
    STREAK_MULT_THRESHOLD = 10
    STREAK_MULT_BONUS = 0.5
    ACCURACY_MULT_FACTOR = 0.01

    def __init__(self, jokers: Optional[List[JokerDef]] = None) -> None:
        self.jokers: List[JokerDef] = jokers or []
        self.state = ScoreState()
        self._last_letter = ""

    def reset(self, jokers: Optional[List[JokerDef]] = None) -> None:
        if jokers is not None:
            self.jokers = jokers
        self.state = ScoreState()
        self._last_letter = ""

    @property
    def chips(self) -> int:
        return self.state.chips

    @property
    def mult(self) -> float:
        return self.state.mult

    @property
    def score(self) -> int:
        return self.state.score

    def _word_just_completed(self, stats: StatsTracker) -> bool:
        return stats.word_count > self.state.prev_word_count

    def _last_word_perfect(self, stats: StatsTracker) -> bool:
        try:
            return stats.last_word_accuracy == 100
        except (ValueError, ZeroDivisionError):
            return False

    def _last_word_length(self, stats: StatsTracker) -> int:
        checkpoints = stats.get_checkpoints_last_word()
        return len(checkpoints)

    def on_keystroke(self, cursor: Cursor, stats: StatsTracker) -> ScoreState:
        """Update score state after a keystroke."""
        # Backspace: break the streak and skip all word-completion logic
        if cursor.new < cursor.old:
            self.state.streak = 0
            self._last_letter = ""
            return self.state

        word_completed = self._word_just_completed(stats)
        last_word_perfect = self._last_word_perfect(stats) if word_completed else False
        last_word_length = self._last_word_length(stats) if word_completed else 0

        if cursor.correct:
            self.state.chips += self.CHIPS_PER_CHAR
            self.state.streak += 1
            char = cursor.letter or self._last_letter
            self._last_letter = char

            if word_completed:
                self.state.chips += self.WORD_BONUS
                self.state.prev_word_count = stats.word_count

            if self.state.streak >= self.STREAK_MULT_THRESHOLD:
                streak_bonus = (
                    self.state.streak // self.STREAK_MULT_THRESHOLD
                ) * self.STREAK_MULT_BONUS
                self.state.base_mult = 1.0 + streak_bonus

            ctx = JokerContext(
                stats=stats,
                streak=self.state.streak,
                last_word_perfect=last_word_perfect,
                last_word_length=last_word_length,
                last_char_was_capital=char.isupper() if char else False,
                word_just_completed=word_completed,
            )
            bonus_chips, bonus_mult = apply_joker_effects(self.jokers, ctx)
            self.state.chips += bonus_chips
            self.state.bonus_mult += bonus_mult
        else:
            self.state.streak = 0
            self.state.base_mult = 1.0

        # Accuracy scales mult continuously
        acc_bonus = stats.accuracy * self.ACCURACY_MULT_FACTOR
        self.state.base_mult = max(1.0, 1.0 + acc_bonus * 0.1)

        return self.state

    def finalize(self, stats: StatsTracker) -> ScoreState:
        """Apply final accuracy bonus at test end."""
        if stats.accuracy >= 95:
            self.state.chips += 50
        elif stats.accuracy >= 90:
            self.state.chips += 25
        return self.state
