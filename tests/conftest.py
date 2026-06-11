import os

import pytest


@pytest.fixture(autouse=True)
def mute_background_music():
    """Keep headless tests free of audio device requirements."""
    os.environ["TYPATRO_MUTE"] = "1"
    yield
    os.environ.pop("TYPATRO_MUTE", None)
