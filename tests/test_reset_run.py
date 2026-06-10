"""Reproduces: pressing 'Reset Run' in settings doesn't fully reset the game.

Expected after reset:
- run state back to ante 1, blind 0, no jokers (state itself)
- boss debuff config tweaks cleared
- sidebar UI (BlindCard / JokerRow) reflects the fresh run
"""

import pytest

from typatro.src import config_parser
from typatro.src.blind import BossBlind, apply_boss_debuff
from typatro.src.run_state import run_manager
from typatro.ui.tui import Typatro
from typatro.ui.widgets.balatro import BlindCard, JokerRow
from typatro.ui.widgets.settings.danger_options import ResetRun


def _dirty_run_state() -> None:
    run_manager.state.ante = 4
    run_manager.state.blind_index = 2
    run_manager.state.joker_ids = ["banner"]
    run_manager.state.total_score = 9000
    # Simulate being on a boss blind with debuffs applied
    apply_boss_debuff(BossBlind.THE_PSYCHIC)


def test_reset_clears_boss_debuffs():
    _dirty_run_state()
    assert config_parser.get("force_correct") == "on"

    run_manager.reset()

    assert run_manager.state.ante == 1
    assert run_manager.state.joker_ids == []
    assert config_parser.get("force_correct") in (False, "off", 0)


@pytest.mark.asyncio
async def test_reset_run_updates_sidebar_ui():
    config_parser.set("game_mode", "run")
    _dirty_run_state()

    app = Typatro()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()

        blind_card = app.screen.query_one(BlindCard)
        joker_row = app.screen.query_one(JokerRow)
        assert blind_card._ante == 4
        assert joker_row._jokers, "precondition: jokers shown in sidebar"

        # Trigger the same callback the settings 'Reset Run' option runs
        ResetRun().save()
        await pilot.pause()

        assert run_manager.state.ante == 1
        assert blind_card._ante == 1, "BlindCard should show ante 1 after reset"
        assert joker_row._jokers == [], "JokerRow should be empty after reset"
