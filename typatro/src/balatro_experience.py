"""Gate Balatro-style audio and TUI animations.

Balatro flourishes (background music, dither backdrop, score pulse, etc.) are
enabled when ``game_mode == "run"``, not by theme. Themes such as ``balatro``
only affect colors; classic mode stays clean and minimal even with that theme.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from typatro.src.parser.config_parser import config_parser

if TYPE_CHECKING:
    from textual.app import App

_run_mode_cached: Optional[bool] = None


def invalidate_balatro_cache() -> None:
    """Clear cached run-mode flag after config changes."""
    global _run_mode_cached
    _run_mode_cached = None


def is_balatro_experience() -> bool:
    """Return True when run-mode Balatro mechanics and flourishes are active."""
    global _run_mode_cached
    if _run_mode_cached is None:
        _run_mode_cached = config_parser.get("game_mode") == "run"
    return _run_mode_cached


def _iter_screens(app: App):
    """Yield every screen on the stack (widgets live under screens, not the app)."""
    stack = getattr(app, "screen_stack", None)
    if stack:
        yield from stack
        return
    screen = getattr(app, "screen", None)
    if screen is not None:
        yield screen


def sync_balatro_experience(app: App | None = None) -> None:
    """Start/stop music and animation timers to match the current game mode."""
    from typatro.src.background_music import start_background_music, stop_background_music

    if is_balatro_experience():
        start_background_music()
    else:
        stop_background_music()

    if app is None:
        return

    try:
        from typatro.ui.tui import MainScreen
        from typatro.ui.widgets.balatro.blind_card import BlindCard
        from typatro.ui.widgets.balatro.dither import DitherBackground
        from typatro.ui.widgets.balatro.score_panel import ScorePanel

        active = is_balatro_experience()
        for screen in _iter_screens(app):
            if isinstance(screen, MainScreen):
                screen.set_class(active, "run-experience")
            for widget in screen.query(DitherBackground):
                widget.set_experience_active(active)
            for panel in screen.query(ScorePanel):
                panel.set_experience_active(active)
            for card in screen.query(BlindCard):
                card.set_experience_active(active)
    except Exception:
        pass
