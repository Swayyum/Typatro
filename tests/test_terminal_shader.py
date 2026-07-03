"""Tests for terminal-native shader backdrop caching."""

import pytest

from typatro.src.dither import DITHER_CHARS, intensity_bucket
from typatro.src.terminal_shader import (
    FRAME_COUNT,
    TerminalShader,
    clear_frame_cache,
    frame_index_for_phase,
    metaballs_intensity,
    plasma_intensity,
    render_shader_lines,
)


def setup_function() -> None:
    clear_frame_cache()


@pytest.mark.parametrize(
    "field_fn",
    [plasma_intensity, metaballs_intensity],
)
def test_shader_intensity_in_unit_range(field_fn):
    for phase in (0.0, 1.7, 42.0):
        for y in range(10):
            for x in range(30):
                value = field_fn(x, y, 30, 10, phase)
                assert 0.0 <= value <= 1.0


def test_shader_intensity_degenerate_size():
    assert plasma_intensity(0, 0, 0, 0, 1.0) == 0.0


def test_frame_index_wraps():
    assert frame_index_for_phase(0.0) == 0
    assert frame_index_for_phase(1000.0) == frame_index_for_phase(0.0)
    assert 0 <= frame_index_for_phase(4.0) < FRAME_COUNT


def test_render_shader_lines_dimensions():
    lines = render_shader_lines(24, 6, 3.0, ["red", "green", "blue"], mode="plasma")
    assert len(lines) == 6
    for line in lines:
        assert line.cell_len == 24
        assert set(line.plain) <= set(DITHER_CHARS)


def test_render_shader_lines_animates_over_phase():
    a = "".join(line.plain for line in render_shader_lines(40, 8, 0.0, ["red"], mode="plasma"))
    b = "".join(line.plain for line in render_shader_lines(40, 8, 4.0, ["red"], mode="plasma"))
    assert a != b


def test_render_shader_lines_mode_metaballs():
    lines = render_shader_lines(20, 5, 1.0, ["#111111"], mode="metaballs")
    assert len(lines) == 5
    buckets = {intensity_bucket(metaballs_intensity(x, 2, 20, 5, 1.0)) for x in range(20)}
    assert buckets <= set(range(len(DITHER_CHARS)))


def test_frame_cache_reuses_build_on_same_key():
    from typatro.src.terminal_shader import cache_key, get_cached_frames

    styles = ("a", "b", "c")
    key = cache_key(12, 4, "plasma", styles)
    first = get_cached_frames(12, 4, "plasma", styles)
    second = get_cached_frames(12, 4, "plasma", styles)
    assert first is second
    assert key in {cache_key(12, 4, "plasma", styles)}


def test_terminal_shader_rebuilds_on_resize():
    shader = TerminalShader(mode="plasma")
    shader.configure(10, 4, ["x", "y", "z"])
    small = shader.render(0.0)
    shader.configure(12, 4, ["x", "y", "z"])
    large = shader.render(0.0)
    assert small[0].cell_len == 10
    assert large[0].cell_len == 12


def test_terminal_shader_rebuilds_on_palette_change():
    shader = TerminalShader(mode="low_power")
    shader.configure(8, 3, ["#010101", "#020202", "#030303"])
    before = shader.render(0.0)
    shader.configure(8, 3, ["#040404", "#050505", "#060606"])
    after = shader.render(0.0)
    assert before[0].plain == after[0].plain
    assert before is not after
