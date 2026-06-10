"""Tests for Balatro scoring, blinds, and jokers."""

from typatro.src.scoring import ScoringEngine
from typatro.src.stats_tracker import StatsTracker, CheckPoint, Match
from typatro.src.tracker import Cursor
from typatro.src.jokers import JokerDef, JokerEffect, apply_joker_effects, JokerContext, pick_random_jokers
from typatro.src.blind import get_blind_for_index, compute_target, SMALL_BLIND
from typatro.src.run_state import RunState


def _make_stats_with_chars(count: int, correct: bool = True) -> StatsTracker:
    stats = StatsTracker()
    stats.start_time = 1.0
    match = Match.MATCH if correct else Match.MISMATCH
    for i in range(count):
        cp = CheckPoint("a", i + 1, match)
        cp.elapsed = 0.1 * (i + 1)
        stats.checkpoints.append(cp)
    return stats


def test_score_increases_on_correct_keystrokes():
    engine = ScoringEngine()
    stats = StatsTracker()
    stats.start_time = 1.0

    cursor = Cursor(0, 1, True, "h")
    cp = CheckPoint("h", 1, Match.MATCH)
    cp.elapsed = 0.1
    stats.checkpoints.append(cp)

    state = engine.on_keystroke(cursor, stats)
    assert state.chips >= 1
    assert state.score == int(state.chips * state.mult)


def test_score_resets_streak_on_error():
    engine = ScoringEngine()
    stats = _make_stats_with_chars(5)

    engine.on_keystroke(Cursor(5, 6, False, "x"), stats)
    assert engine.state.streak == 0


def test_joker_flat_mult():
    joker = JokerDef("test", "Test", "+4 Mult", JokerEffect.FLAT_MULT, 4)
    stats = StatsTracker()
    stats.start_time = 1.0
    ctx = JokerContext(stats=stats, streak=5, last_word_perfect=False,
                       last_word_length=0, last_char_was_capital=False,
                       word_just_completed=False)
    chips, mult = apply_joker_effects([joker], ctx)
    assert mult == 4
    assert chips == 0


def test_pick_random_jokers():
    picks = pick_random_jokers(3)
    assert len(picks) == 3
    assert len(set(j.id for j in picks)) == 3


def test_blind_target_scales():
    target_30 = compute_target(SMALL_BLIND, 30)
    target_60 = compute_target(SMALL_BLIND, 60)
    assert target_60 == target_30 * 2


def test_run_state_advance():
    run = RunState()
    run.blind_index = 0
    assert run.current_blind.name == "Small Blind"
    beaten = run.advance_blind(500)
    assert beaten is True
    assert run.blind_index == 1


def test_run_state_joker_limit():
    run = RunState()
    for i in range(6):
        run.add_joker(f"joker_{i}")
    assert len(run.joker_ids) <= 5


def test_backspace_over_word_boundary_does_not_crash():
    """Regression: backspacing across a word boundary divided by zero.

    Typing 'ab ' then backspacing leaves only BACKSPACE checkpoints in the
    last word, which crashed last_word_accuracy with ZeroDivisionError.
    """
    engine = ScoringEngine()
    stats = StatsTracker()
    stats.start_time = 1.0

    for i, letter in enumerate("ab "):
        cp = CheckPoint(letter, i + 1, Match.MATCH)
        cp.elapsed = 0.1 * (i + 1)
        stats.checkpoints.append(cp)
        engine.on_keystroke(Cursor(i, i + 1, True, letter), stats)

    # Backspace from position 3 back to 2 — crosses the word boundary
    backspace_cp = CheckPoint("", 2, Match.BACKSPACE)
    backspace_cp.elapsed = 0.4
    stats.checkpoints.append(backspace_cp)

    state = engine.on_keystroke(Cursor(3, 2, True, ""), stats)
    assert state.streak == 0


def test_last_word_accuracy_with_only_backspaces_raises_value_error():
    stats = StatsTracker()
    stats.start_time = 1.0
    cp = CheckPoint("", 2, Match.BACKSPACE)
    cp.elapsed = 0.1
    stats.checkpoints.append(cp)

    import pytest as _pytest

    with _pytest.raises(ValueError):
        stats.last_word_accuracy


def test_reel_spin_locks_left_to_right():
    from typatro.src.slot_machine import ReelSpin

    reel = ReelSpin(target="typatro")
    frames = 0
    while not reel.done and frames < 200:
        out = reel.tick()
        frames += 1
        assert len(out) == len("typatro")
        locked = reel.locked_count()
        assert out[: min(locked, 7)] == "typatro"[: min(locked, 7)]
    assert reel.done


def test_odometer_rolls_to_target():
    from typatro.src.slot_machine import Odometer

    odo = Odometer()
    odo.set_target(1000)
    last = 0
    for _ in range(100):
        value = odo.tick()
        assert value >= last
        last = value
        if odo.done:
            break
    assert last == 1000


def test_digit_spin_settles_on_target():
    from typatro.src.slot_machine import DigitSpin

    spin = DigitSpin.for_number(427)
    out = ""
    for _ in range(200):
        out = spin.tick()
        if spin.done:
            break
    assert spin.done
    assert out == "427"
