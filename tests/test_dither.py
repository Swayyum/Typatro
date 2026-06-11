"""Tests for the swirling dither backdrop logic and animated widgets."""

import pytest

from typatro.src.dither import (
    DITHER_CHARS,
    intensity_bucket,
    render_lines,
    swirl_intensity,
)


def test_swirl_intensity_in_unit_range():
    for phase in (0.0, 1.7, 42.0):
        for y in range(10):
            for x in range(30):
                value = swirl_intensity(x, y, 30, 10, phase)
                assert 0.0 <= value <= 1.0


def test_swirl_intensity_degenerate_size():
    assert swirl_intensity(0, 0, 0, 0, 1.0) == 0.0


def test_intensity_bucket_covers_all_chars():
    buckets = {intensity_bucket(v / 100.0) for v in range(101)}
    assert buckets == set(range(len(DITHER_CHARS)))


def test_render_lines_dimensions_and_width():
    lines = render_lines(24, 6, 3.0, ["red", "green", "blue"])
    assert len(lines) == 6
    for line in lines:
        assert line.cell_len == 24
        assert set(line.plain) <= set(DITHER_CHARS)


def test_render_lines_animates_over_phase():
    a = "".join(line.plain for line in render_lines(40, 8, 0.0, ["red"]))
    b = "".join(line.plain for line in render_lines(40, 8, 2.0, ["red"]))
    assert a != b


def test_render_lines_no_styles():
    lines = render_lines(10, 2, 0.5, [])
    assert len(lines) == 2


def _composite_plain(composite) -> str:
    return "".join("".join(seg.text for seg in strip._segments) for strip in composite)


def _blob_only_line_count(composite) -> int:
    """Lines filled only with dither/spaces — the full-screen blob regression."""
    count = 0
    for strip in composite:
        line = "".join(seg.text for seg in strip._segments)
        if line.strip() and all(char in " ░▒▓" for char in line):
            count += 1
    return count


@pytest.mark.asyncio
async def test_main_screen_backdrop_visible_in_run_mode():
    """Main screen must expose the swirling dither through semi-transparent layers."""
    from typatro.src import config_parser
    from typatro.src.dither import DITHER_CHARS
    from typatro.ui.tui import Typatro
    from typatro.ui.widgets.balatro import DitherBackground
    from typatro.ui.widgets.base_window import BaseWindow
    from typatro.ui.tui import PassthroughContentSwitcher

    config_parser.set("game_mode", "run")
    app = Typatro()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        assert app.screen.has_class("run-experience")
        assert app.screen.styles.background.a < 1.0

        backdrop = app.screen.query_one(DitherBackground)
        assert backdrop.display
        assert backdrop.size == app.screen.size
        assert backdrop.styles.overlay == "none"

        content_switcher = app.screen.query_one(PassthroughContentSwitcher)
        typing_screen = app.screen.query_one("TypingScreen")
        assert content_switcher.styles.background.a == 0
        assert typing_screen.styles.background.a == 0
        assert isinstance(typing_screen, BaseWindow)

        phase_before = backdrop._phase
        backdrop._tick()
        assert backdrop._phase > phase_before

        rendered = backdrop.render()
        plain = "".join(line.plain for line in rendered.renderables)
        shaded = sum(plain.count(c) for c in DITHER_CHARS if c != " ")
        assert shaded > 0

        composite = app.screen._compositor.render_strips()
        composite_plain = _composite_plain(composite)
        composite_shaded = sum(composite_plain.count(c) for c in DITHER_CHARS if c != " ")
        assert composite_shaded > 0
        assert "home" in composite_plain.lower()
        assert _blob_only_line_count(composite) < len(composite) // 2


@pytest.mark.asyncio
async def test_main_screen_no_run_experience_in_classic_mode():
    from typatro.src import config_parser
    from typatro.ui.tui import Typatro

    config_parser.set("game_mode", "classic")
    app = Typatro()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        assert not app.screen.has_class("run-experience")


@pytest.mark.asyncio
async def test_dither_background_mounts_on_main_screen():
    from typatro.src import config_parser
    from typatro.ui.tui import Typatro
    from typatro.ui.widgets.balatro import DitherBackground

    config_parser.set("game_mode", "run")
    app = Typatro()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        backdrops = app.screen.query(DitherBackground)
        assert len(backdrops) == 1
        backdrop = backdrops[0]
        assert backdrop.size.width > 0
        backdrop._tick()
        assert backdrop._phase > 0.0


@pytest.mark.asyncio
async def test_main_screen_has_single_dither_not_in_sidebar():
    from typatro.src import config_parser
    from typatro.ui.tui import Typatro
    from typatro.ui.widgets.balatro import DitherBackground

    config_parser.set("game_mode", "run")
    app = Typatro()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        assert len(app.screen.query(DitherBackground)) == 1
        from typatro.ui.screens.typing import GameSidebar

        sidebar = app.screen.query_one(GameSidebar)
        assert len(sidebar.query(DitherBackground)) == 0


@pytest.mark.asyncio
async def test_blind_card_pulses_on_update():
    from typatro.src import config_parser
    from typatro.src.blind import BlindDef, BlindType
    from typatro.ui.tui import Typatro
    from typatro.ui.widgets.balatro import BlindCard

    config_parser.set("game_mode", "run")
    app = Typatro()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        card = app.screen.query_one(BlindCard)
        blind = BlindDef(
            blind_type=BlindType.SMALL,
            name="Small Blind",
            target_multiplier=1.0,
            reward="$3",
        )
        card.update_blind(blind, target=500, ante=2)
        assert card.has_class("pulse")
        card._end_pulse()
        assert not card.has_class("pulse")


@pytest.mark.asyncio
async def test_joker_choice_screen_has_dither_backdrop():
    from typatro.src import config_parser
    from typatro.ui.screens.joker_choice import JokerChoiceScreen
    from typatro.ui.tui import Typatro
    from typatro.ui.widgets.balatro import DitherBackground

    config_parser.set("game_mode", "run")
    app = Typatro()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        app.push_screen(JokerChoiceScreen())
        await pilot.pause()
        backdrop = app.screen.query_one(DitherBackground)
        assert backdrop.size.width > 0
        assert backdrop.styles.overlay == "none"
        composite = app.screen._compositor.render_strips()
        composite_plain = _composite_plain(composite)
        assert "Choose a Joker" in composite_plain
        assert sum(composite_plain.count(c) for c in DITHER_CHARS if c != " ") > 0
        app.screen.action_skip()
        await pilot.pause()


@pytest.mark.asyncio
async def test_main_and_joker_composite_shows_dither_and_ui():
    """Regression: both screens show UI content with subtle dither, not a full-screen blob."""
    from typatro.src import config_parser
    from typatro.ui.screens.joker_choice import JokerChoiceScreen
    from typatro.ui.tui import Typatro

    config_parser.set("game_mode", "run")
    app = Typatro()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        main_composite = app.screen._compositor.render_strips()
        main_plain = _composite_plain(main_composite)
        assert any(c in main_plain for c in DITHER_CHARS if c != " ")
        assert "home" in main_plain.lower()
        assert _blob_only_line_count(main_composite) < len(main_composite) // 2

        app.push_screen(JokerChoiceScreen())
        await pilot.pause()
        joker_composite = app.screen._compositor.render_strips()
        joker_plain = _composite_plain(joker_composite)
        assert any(c in joker_plain for c in DITHER_CHARS if c != " ")
        assert "Choose a Joker" in joker_plain
        app.screen.action_skip()
        await pilot.pause()


@pytest.mark.asyncio
async def test_joker_choice_cards_layout_horizontally():
    from typatro.src import config_parser
    from typatro.ui.screens.joker_choice import JokerChoiceScreen, JokerOption
    from typatro.ui.tui import Typatro

    config_parser.set("game_mode", "run")
    app = Typatro()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        app.push_screen(JokerChoiceScreen())
        await pilot.pause()
        options = list(app.screen.query(JokerOption))
        assert len(options) == 3
        row = app.screen.query_one("#joker-options")
        assert row.size.width >= 3 * JokerOption.CARD_WIDTH
        assert row.size.height == JokerOption.CARD_HEIGHT
        y_coords = {o.region.y for o in options}
        assert len(y_coords) == 1
        for option in options:
            assert option.size.width == JokerOption.CARD_WIDTH
            assert option.size.height == JokerOption.CARD_HEIGHT
        x_coords = [o.region.x for o in options]
        assert x_coords == sorted(x_coords)
        assert x_coords[1] > x_coords[0]
        app.screen.action_skip()
        await pilot.pause()


@pytest.mark.asyncio
async def test_dither_inactive_in_classic_mode():
    from typatro.src import config_parser
    from typatro.ui.tui import Typatro
    from typatro.ui.widgets.balatro import DitherBackground

    config_parser.set("game_mode", "classic")
    app = Typatro()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        backdrop = app.screen.query_one(DitherBackground)
        assert not backdrop.display
        phase_before = backdrop._phase
        if backdrop._timer is not None:
            backdrop._tick()
        assert backdrop._phase == phase_before
        assert backdrop._timer is None


def test_background_music_not_started_in_classic_mode(monkeypatch):
    from typatro.src import background_music, config_parser

    monkeypatch.delenv("TYPATRO_MUTE", raising=False)
    background_music._instance = None
    config_parser.set("game_mode", "classic")
    background_music.start_background_music()
    assert background_music._instance is None


@pytest.mark.asyncio
async def test_blind_card_no_pulse_in_classic_mode():
    from typatro.src import config_parser
    from typatro.src.blind import BlindDef, BlindType
    from typatro.ui.tui import Typatro
    from typatro.ui.widgets.balatro import BlindCard

    config_parser.set("game_mode", "classic")
    app = Typatro()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        card = app.screen.query_one(BlindCard)
        blind = BlindDef(
            blind_type=BlindType.SMALL,
            name="Small Blind",
            target_multiplier=1.0,
            reward="$3",
        )
        card.update_blind(blind, target=500, ante=2)
        assert not card.has_class("pulse")


@pytest.mark.asyncio
async def test_sync_activates_dither_after_classic_to_run_toggle():
    """Toggling run mode must re-enable backdrop and timers via sync."""
    from typatro.src import config_parser
    from typatro.src.balatro_experience import sync_balatro_experience
    from typatro.ui.tui import Typatro
    from typatro.ui.widgets.balatro import DitherBackground
    from typatro.ui.widgets.typing.config_strip import RunMode

    config_parser.set("game_mode", "classic")
    app = Typatro()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        backdrop = app.screen.query_one(DitherBackground)
        assert not backdrop.display

        config_parser.set("game_mode", "run")
        sync_balatro_experience(app)
        await pilot.pause()
        assert backdrop.display
        assert backdrop._timer is not None
        assert backdrop.size.width > 0

        phase_before = backdrop._phase
        backdrop._tick()
        assert backdrop._phase > phase_before


@pytest.mark.asyncio
async def test_run_mode_toggle_via_strip_reactivates_dither():
    """Clicking the run-mode strip switch must restore Balatro animations."""
    from typatro.src import config_parser
    from typatro.ui.tui import Typatro
    from typatro.ui.widgets.balatro import DitherBackground
    from typatro.ui.widgets.typing.config_strip import RunMode

    config_parser.set("game_mode", "classic")
    app = Typatro()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        backdrop = app.screen.query_one(DitherBackground)
        assert not backdrop.display

        run_mode = app.screen.query_one(RunMode)
        run_mode.on_click()
        await pilot.pause()

        assert config_parser.get("game_mode") == "run"
        assert backdrop.display
        assert backdrop._timer is not None
        assert backdrop.size.width > 0
        phase_before = backdrop._phase
        backdrop._tick()
        assert backdrop._phase > phase_before


@pytest.mark.asyncio
async def test_score_panel_pulses_while_rolling():
    from typatro.src import config_parser
    from typatro.src.scoring import ScoreState
    from typatro.ui.tui import Typatro
    from typatro.ui.widgets.balatro import ScorePanel

    config_parser.set("game_mode", "run")
    app = Typatro()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        panel = app.screen.query_one(ScorePanel)
        panel.update_score(ScoreState(chips=100, base_mult=2.0))
        assert panel.has_class("rolling")
        while not panel._odometer.done:
            panel._roll_tick()
        assert not panel.has_class("rolling")
