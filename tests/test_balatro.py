"""Tests for Balatro scoring, blinds, and jokers."""

import pytest

from typatro.src.scoring import ScoringEngine, ScoreState
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


def test_streak_mult_increases_at_threshold():
    """Streak bonus must stack with accuracy mult, not be overwritten."""
    engine = ScoringEngine()
    stats = StatsTracker()
    stats.start_time = 1.0

    for i in range(10):
        cp = CheckPoint("a", i + 1, Match.MATCH)
        cp.elapsed = 0.1 * (i + 1)
        stats.checkpoints.append(cp)
        engine.on_keystroke(Cursor(i, i + 1, True, "a"), stats)

    assert engine.state.streak == 10
    # 1.0 base + 0.5 streak tier + 0.1 accuracy at 100%
    assert engine.mult >= 1.5


def test_score_and_mult_increase_over_many_keystrokes():
    engine = ScoringEngine()
    stats = StatsTracker()
    stats.start_time = 1.0
    prev_score = 0
    prev_mult = 1.0

    for i in range(15):
        cp = CheckPoint("a", i + 1, Match.MATCH)
        cp.elapsed = 0.1 * (i + 1)
        stats.checkpoints.append(cp)
        state = engine.on_keystroke(Cursor(i, i + 1, True, "a"), stats)
        assert state.score >= prev_score
        assert state.mult >= prev_mult
        prev_score = state.score
        prev_mult = state.mult

    assert prev_score > 0
    assert prev_mult > 1.0


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
    beaten = run.advance_blind(run.target_score())
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


def test_logo_reel_locks_left_to_right():
    from typatro.src.slot_machine import LogoReelEngine

    engine = LogoReelEngine(target="typatro")
    frames = 0
    while not engine.done and frames < 400:
        engine.tick()
        frames += 1
        locked = sum(1 for col in engine.columns if col.state == "stopped")
        for index in range(locked):
            assert engine.columns[index].display == engine.columns[index].target.upper()
    assert engine.done
    assert [col.display for col in engine.columns] == [c.upper() for c in "typatro"]


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


def test_format_number_comma_grouping_below_threshold():
    from typatro.src.scoring import format_number

    assert format_number(0) == "0"
    assert format_number(999) == "999"
    assert format_number(1234567) == "1,234,567"
    assert format_number(99_999_999_999) == "99,999,999,999"
    assert format_number(1234567, sep="") == "1234567"


def test_format_number_scientific_above_threshold():
    from typatro.src.scoring import format_number

    assert format_number(10**11) == "1.000e11"
    assert format_number(1_234_000_000_000_0) == "1.234e13"
    assert format_number(-1_234_000_000_000_0) == "-1.234e13"
    # Beyond float range — must not lose precision or overflow
    assert format_number(10**308) == "1.000e308"
    assert format_number(987 * 10**400) == "9.870e402"


def test_score_state_exact_for_huge_chips():
    from typatro.src.scoring import ScoreState

    state = ScoreState(chips=10**18, base_mult=1.5)
    assert state.score == 10**18 * 150 // 100
    # Far beyond float precision (2**53) — exact integer math required
    state = ScoreState(chips=10**100, base_mult=2.0)
    assert state.score == 2 * 10**100


def test_high_ante_targets_scale_exponentially():
    run = RunState()
    run.ante = 1
    base = compute_target(SMALL_BLIND, 30, ante=1)
    assert compute_target(SMALL_BLIND, 30, ante=2) > base
    # Exact integer scaling, no float drift even at absurd antes
    huge = compute_target(SMALL_BLIND, 30, ante=2000)
    assert isinstance(huge, int)
    assert huge > 10**300


def test_run_state_target_uses_ante():
    run_low = RunState(ante=1)
    run_high = RunState(ante=8)
    assert run_high.target_score() > run_low.target_score()


def test_run_state_save_load_huge_total_score(tmp_path):
    import json

    run = RunState(total_score=10**320)
    blob = json.dumps(run.to_dict())
    restored = RunState.from_dict(json.loads(blob))
    assert restored.total_score == 10**320


def test_odometer_converges_for_huge_targets():
    from typatro.src.slot_machine import Odometer

    target = 10**308
    odo = Odometer()
    odo.set_target(target)
    last = 0
    ticks = 0
    while not odo.done and ticks < 4000:
        value = odo.tick()
        assert value >= last
        last = value
        ticks += 1
    assert odo.done
    assert odo.value == target  # exact, no float precision loss


def test_odometer_exact_at_float_precision_boundary():
    from typatro.src.slot_machine import Odometer

    target = 2**53 + 1  # not representable as a float
    odo = Odometer()
    odo.set_target(target)
    for _ in range(1000):
        odo.tick()
        if odo.done:
            break
    assert odo.value == target


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


class _FakeRollTimer:
    def resume(self) -> None:
        pass

    def pause(self) -> None:
        pass


def test_score_panel_syncs_display_when_odometer_already_done(monkeypatch):
    """Regression: ROUND SCORE must not stay stale when value already hit target."""
    from typatro.ui.widgets.balatro.score_panel import ScorePanel

    monkeypatch.setattr(
        "typatro.ui.widgets.balatro.score_panel.is_balatro_experience",
        lambda: True,
    )

    panel = ScorePanel()
    panel._roll_timer = _FakeRollTimer()

    state = ScoreState(chips=10, base_mult=1.0)
    panel._odometer.value = 10
    panel._odometer.target = 10
    panel._display_score = 0

    panel.update_score(state)

    assert state.score == 10
    assert panel._display_score == 10


def test_score_panel_advances_display_on_keystroke_without_timer(monkeypatch):
    """Regression: each score update must move ROUND SCORE, not only the target."""
    from typatro.ui.widgets.balatro.score_panel import ScorePanel

    monkeypatch.setattr(
        "typatro.ui.widgets.balatro.score_panel.is_balatro_experience",
        lambda: True,
    )

    panel = ScorePanel()
    panel._roll_timer = _FakeRollTimer()

    for expected in range(1, 6):
        state = ScoreState(chips=expected, base_mult=1.0)
        panel.update_score(state)
        assert panel._odometer.target == expected
        assert panel._display_score > 0


@pytest.mark.asyncio
async def test_typing_increases_round_score_during_run():
    """Integration: typing in run mode raises engine score and ROUND SCORE."""
    from typatro.src import config_parser
    from typatro.ui.tui import Typatro
    from typatro.ui.widgets import Space
    from typatro.ui.widgets.balatro import ScorePanel

    config_parser.set("game_mode", "run")
    app = Typatro()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        space = app.screen.query_one(Space)
        panel = app.screen.query_one(ScorePanel)

        for char in space.paragraph.plain[:8]:
            space.keypress(char)

        assert space.scoring.score >= 8
        assert panel._chips >= 8
        assert panel._display_score > 0
        assert panel._odometer.target == space.scoring.score

        await pilot.pause(delay=0.5)
        assert panel._display_score == space.scoring.score
