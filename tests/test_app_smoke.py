"""Headless smoke tests for the Typatro TUI."""

import pytest

from typatro.src import config_parser
from typatro.ui.tui import Typatro


@pytest.mark.asyncio
async def test_app_boots_in_run_mode():
    config_parser.set("game_mode", "run")
    app = Typatro()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        from typatro.ui.widgets.balatro import ScorePanel, BlindCard, JokerRow

        assert app.screen.query_one(ScorePanel) is not None
        assert app.screen.query_one(BlindCard) is not None
        assert app.screen.query_one(JokerRow) is not None


@pytest.mark.asyncio
async def test_typing_updates_score():
    config_parser.set("game_mode", "run")
    app = Typatro()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        from typatro.ui.widgets import Space
        from typatro.ui.widgets.balatro import ScorePanel

        space = app.screen.query_one(Space)
        first_char = space.paragraph.plain[0]
        space.keypress(first_char)
        await pilot.pause()

        panel = app.screen.query_one(ScorePanel)
        assert panel._chips >= 1


@pytest.mark.asyncio
async def test_app_boots_in_classic_mode():
    config_parser.set("game_mode", "classic")
    app = Typatro()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        from typatro.ui.widgets import Space

        space = app.screen.query_one(Space)
        first_char = space.paragraph.plain[0]
        space.keypress(first_char)
        await pilot.pause()
        assert space.tracker.cursor_pos == 1

    config_parser.set("game_mode", "run")
