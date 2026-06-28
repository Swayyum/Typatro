"""Non-blocking looping background music for the Typatro TUI."""

from __future__ import annotations

import os
import threading
from importlib.resources import files
from pathlib import Path
from typing import Optional

# typatro/assets/background.mp3
_ASSET = "background.mp3"

_instance: Optional["BackgroundMusic"] = None


def _is_env_muted() -> bool:
    """Return True when TYPATRO_MUTE forces silence (tests, CI, user override).

    ``TYPATRO_MUTE=1`` overrides the saved ``music_muted`` / ``music_volume``
    config at runtime; it does not rewrite the user's settings file.
    """
    value = os.environ.get("TYPATRO_MUTE", "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _config_muted() -> bool:
    from typatro.src.parser.config_parser import config_parser

    muted = config_parser.get("music_muted")
    if isinstance(muted, bool):
        return muted
    return muted == "on"


def _config_volume_ratio() -> float:
    from typatro.src.parser.config_parser import config_parser

    volume = config_parser.get("music_volume")
    if volume is None:
        return 1.0
    return max(0.0, min(1.0, float(volume) / 100.0))


def is_effectively_muted() -> bool:
    """True when playback should be silent (env override, mute flag, or volume 0)."""
    if _is_env_muted():
        return True
    if _config_muted():
        return True
    return _config_volume_ratio() == 0.0


def get_effective_volume() -> float:
    """Pygame mixer volume in 0.0–1.0 after env/config mute rules."""
    if is_effectively_muted():
        return 0.0
    return _config_volume_ratio()


def _music_path() -> Path:
    return Path(files("typatro.assets").joinpath(_ASSET))


class BackgroundMusic:
    """Runs pygame.mixer on a daemon thread so the Textual event loop never blocks."""

    def __init__(self) -> None:
        self._active = False
        self._thread: Optional[threading.Thread] = None
        self._volume = 1.0

    def set_volume(self, volume: float) -> None:
        self._volume = max(0.0, min(1.0, volume))
        try:
            import pygame

            if pygame.mixer.get_init():
                pygame.mixer.music.set_volume(self._volume)
        except Exception:
            pass

    def start(self) -> None:
        if is_effectively_muted():
            return

        self._volume = get_effective_volume()

        if self._thread is not None:
            self.set_volume(self._volume)
            return

        path = _music_path()
        if not path.is_file():
            return

        self._active = True
        volume = self._volume

        def _run() -> None:
            try:
                import pygame

                pygame.mixer.init()
                pygame.mixer.music.load(str(path))
                pygame.mixer.music.set_volume(volume)
                pygame.mixer.music.play(-1)
                while self._active and pygame.mixer.music.get_busy():
                    pygame.time.wait(200)
                if pygame.mixer.get_init():
                    pygame.mixer.music.stop()
                    pygame.mixer.quit()
            except Exception:
                pass

        thread = threading.Thread(target=_run, name="typatro-bg-music", daemon=True)
        self._thread = thread
        thread.start()

    def stop(self) -> None:
        self._active = False
        thread = self._thread
        if thread is None:
            return
        thread.join(timeout=2.0)
        self._thread = None


def apply_music_settings() -> None:
    """Apply current config volume/mute immediately (run mode only)."""
    from typatro.src.balatro_experience import is_balatro_experience

    if not is_balatro_experience():
        return

    global _instance

    if is_effectively_muted():
        if _instance is not None:
            _instance.stop()
            _instance = None
        return

    if _instance is None:
        _instance = BackgroundMusic()
    _instance.start()
    _instance.set_volume(get_effective_volume())


def start_background_music() -> None:
    from typatro.src.balatro_experience import is_balatro_experience

    if not is_balatro_experience():
        return

    apply_music_settings()


def stop_background_music() -> None:
    global _instance
    if _instance is not None:
        _instance.stop()
        _instance = None
