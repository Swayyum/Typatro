"""Tests for background music config and volume application."""

import pytest

from typatro.src import background_music, config_parser


@pytest.fixture(autouse=True)
def restore_music_config():
    original_muted = config_parser.get("music_muted")
    original_volume = config_parser.get("music_volume")
    original_game_mode = config_parser.get("game_mode")
    yield
    config_parser.set("music_muted", original_muted)
    config_parser.set("music_volume", original_volume)
    config_parser.set("game_mode", original_game_mode)
    background_music._instance = None


def test_config_defaults_include_music_settings():
    assert config_parser.DEFAULT_CONFIG["music_muted"] is False
    assert config_parser.DEFAULT_CONFIG["music_volume"] == 100


def test_effective_volume_from_config(monkeypatch):
    monkeypatch.delenv("TYPATRO_MUTE", raising=False)
    config_parser.set("music_muted", False)
    config_parser.set("music_volume", 50)
    assert background_music.get_effective_volume() == pytest.approx(0.5)


def test_effective_volume_zero_when_config_muted(monkeypatch):
    monkeypatch.delenv("TYPATRO_MUTE", raising=False)
    config_parser.set("music_muted", "on")
    config_parser.set("music_volume", 100)
    assert background_music.is_effectively_muted() is True
    assert background_music.get_effective_volume() == 0.0


def test_effective_volume_zero_when_volume_is_zero(monkeypatch):
    monkeypatch.delenv("TYPATRO_MUTE", raising=False)
    config_parser.set("music_muted", False)
    config_parser.set("music_volume", 0)
    assert background_music.is_effectively_muted() is True

def test_env_mute_overrides_config(monkeypatch):
    monkeypatch.setenv("TYPATRO_MUTE", "1")
    config_parser.set("music_muted", False)
    config_parser.set("music_volume", 100)
    assert background_music.is_effectively_muted() is True
    assert background_music.get_effective_volume() == 0.0


def test_apply_music_settings_noop_in_classic_mode(monkeypatch):
    monkeypatch.delenv("TYPATRO_MUTE", raising=False)
    background_music._instance = None
    config_parser.set("game_mode", "classic")
    config_parser.set("music_muted", False)
    config_parser.set("music_volume", 100)
    background_music.apply_music_settings()
    assert background_music._instance is None


def test_toggle_music_muted(monkeypatch):
    monkeypatch.delenv("TYPATRO_MUTE", raising=False)
    config_parser.set("music_muted", False)
    config_parser.toggle_music_muted()
    assert config_parser.get("music_muted") is True
    config_parser.toggle_music_muted()
    assert config_parser.get("music_muted") is False
