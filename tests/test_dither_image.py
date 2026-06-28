"""Tests for optional image-backed dither backgrounds."""

import pytest

from typatro.src.dither import DITHER_CHARS
from typatro.src.dither_image import (
    POI_BACKGROUND_ASSETS,
    clear_sample_cache,
    composite_intensity,
    poi_background_path,
    render_lines_for_theme,
)


def setup_function() -> None:
    clear_sample_cache()


def test_poi_background_assets_empty():
    assert POI_BACKGROUND_ASSETS == {}
    assert poi_background_path("veridia") is None


def test_composite_intensity_in_unit_range():
    for phase in (0.0, 1.3, 9.0):
        for y in range(8):
            for x in range(20):
                value = composite_intensity(x, y, 0.5, phase)
                assert 0.0 <= value <= 1.0


def test_render_lines_for_theme_missing_asset_falls_back_to_procedural(monkeypatch):
    monkeypatch.setattr(
        "typatro.src.dither_image.poi_background_path",
        lambda _theme: None,
    )
    clear_sample_cache()
    lines = render_lines_for_theme("veridia", 10, 4, 0.5, ["a", "b", "c", "d", "e"])
    assert len(lines) == 4
    for line in lines:
        assert line.cell_len == 10


@pytest.mark.asyncio
async def test_veridia_theme_uses_swirl_backdrop_in_run_mode():
    from typatro.src import config_parser
    from typatro.ui.tui import Typatro
    from typatro.ui.widgets.balatro import DitherBackground

    config_parser.set("game_mode", "run")
    config_parser.set("theme", "veridia")
    app = Typatro()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        backdrop = app.screen.query_one(DitherBackground)
        assert backdrop.display
        rendered = backdrop.render()
        plain = "".join(line.plain for line in rendered.renderables)
        assert any(c in plain for c in DITHER_CHARS if c != " ")
