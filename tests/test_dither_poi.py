"""Tests for procedural grain dither helpers."""

from typatro.src.dither_poi import (
    ZONE_COUNT,
    is_poi_theme,
    poi_intensity,
    poi_zone,
    render_lines,
)


def test_is_poi_theme_recognizes_no_themes():
    assert not is_poi_theme("bathyn")
    assert not is_poi_theme("veridia")
    assert not is_poi_theme("balatro")
    assert not is_poi_theme(None)


def test_poi_intensity_in_unit_range():
    for phase in (0.0, 1.7, 42.0):
        for y in range(10):
            for x in range(30):
                value = poi_intensity(x, y, 30, 10, phase)
                assert 0.0 <= value <= 1.0


def test_poi_zone_covers_all_zones():
    zones = {
        poi_zone(x, y, 48, 16, 1.5)
        for y in range(16)
        for x in range(48)
    }
    assert zones == set(range(ZONE_COUNT))


def test_poi_field_animates_over_phase():
    changed = any(
        poi_zone(x, y, 40, 12, 0.0) != poi_zone(x, y, 40, 12, 3.0)
        for y in range(12)
        for x in range(40)
    )
    assert changed


def test_poi_render_lines_dimensions():
    lines = render_lines(24, 6, 3.0, ["a", "b", "c", "d", "e"])
    assert len(lines) == 6
    for line in lines:
        assert line.cell_len == 24
