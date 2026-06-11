"""Tests for image-backed POI Studio dither backgrounds."""

import pytest

from typatro.src.dither import DITHER_CHARS
from typatro.src.dither_image import (
    POI_BACKGROUND_ASSETS,
    clear_sample_cache,
    composite_intensity,
    poi_background_path,
    render_lines,
    render_lines_for_theme,
    sample_image_grid,
)


def setup_function() -> None:
    clear_sample_cache()


def test_poi_background_assets_exist_for_both_themes():
    for theme, filename in POI_BACKGROUND_ASSETS.items():
        path = poi_background_path(theme)
        assert path is not None
        assert path.name == filename
        assert path.is_file(), f"missing bundled asset for {theme}"


def test_sample_image_grid_dimensions():
    grid = sample_image_grid("bathyn", 32, 12)
    assert grid is not None
    assert len(grid) == 12
    assert all(len(row) == 32 for row in grid)
    for row in grid:
        for r, g, b in row:
            assert 0 <= r <= 255
            assert 0 <= g <= 255
            assert 0 <= b <= 255


def test_sample_image_grid_uses_cache():
    first = sample_image_grid("veridia", 20, 8)
    second = sample_image_grid("veridia", 20, 8)
    assert first is second
    clear_sample_cache()
    third = sample_image_grid("veridia", 20, 8)
    assert third is not first


def test_sample_image_grid_refreshes_on_resize():
    small = sample_image_grid("bathyn", 16, 6)
    large = sample_image_grid("bathyn", 24, 6)
    assert small is not large
    assert len(small[0]) == 16
    assert len(large[0]) == 24


def test_composite_intensity_in_unit_range():
    for phase in (0.0, 1.3, 9.0):
        for y in range(8):
            for x in range(20):
                value = composite_intensity(x, y, 0.5, phase)
                assert 0.0 <= value <= 1.0


def test_render_lines_dimensions_and_chars():
    grid = sample_image_grid("bathyn", 28, 10)
    assert grid is not None
    lines = render_lines(28, 10, 2.0, grid)
    assert len(lines) == 10
    for line in lines:
        assert line.cell_len == 28
        assert set(line.plain) <= set(DITHER_CHARS)


def test_render_lines_animates_over_phase():
    grid = sample_image_grid("veridia", 36, 10)
    assert grid is not None
    a = "".join(line.plain for line in render_lines(36, 10, 0.0, grid))
    b = "".join(line.plain for line in render_lines(36, 10, 3.0, grid))
    assert a != b


def test_render_lines_for_theme_uses_image_colors():
    lines = render_lines_for_theme("bathyn", 24, 6, 1.0, ["shadow"])
    assert len(lines) == 6
    assert any(line.spans for line in lines)


def test_render_lines_for_theme_missing_asset_falls_back_to_procedural(monkeypatch):
    monkeypatch.setattr(
        "typatro.src.dither_image.poi_background_path",
        lambda _theme: None,
    )
    clear_sample_cache()
    lines = render_lines_for_theme("bathyn", 10, 4, 0.5, ["a", "b", "c", "d", "e"])
    assert len(lines) == 4
    for line in lines:
        assert line.cell_len == 10


@pytest.mark.asyncio
async def test_bathyn_theme_backdrop_uses_image_dither():
    from typatro.src import config_parser
    from typatro.ui.tui import Typatro
    from typatro.ui.widgets.balatro import DitherBackground

    config_parser.set("game_mode", "run")
    config_parser.set("theme", "bathyn")
    app = Typatro()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        backdrop = app.screen.query_one(DitherBackground)
        assert backdrop.display
        rendered = backdrop.render()
        plain = "".join(line.plain for line in rendered.renderables)
        assert any(c in plain for c in DITHER_CHARS if c != " ")
        assert any(line.spans for line in rendered.renderables)
        phase_before = backdrop._phase
        backdrop._tick()
        assert backdrop._phase > phase_before
