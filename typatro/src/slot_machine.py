"""Slot machine animation primitives for TYPATRO.

Provides frame-based reel spin and odometer count-up logic that widgets
drive from a Textual interval timer. Pure logic — no widget dependencies —
so it stays unit-testable.
"""

from __future__ import annotations

import math
import string
import time
from dataclasses import dataclass, field
from random import choice, randint
from typing import List, Literal

from rich.text import Text

REEL_SYMBOLS = string.ascii_lowercase
LOGO_SYMBOLS = string.ascii_uppercase
DIGIT_SYMBOLS = string.digits

ColumnState = Literal["spin", "stopping", "stopped"]


def hsv_to_hex(h: float, s: float = 1.0, v: float = 1.0) -> str:
    """HSV (h in degrees) -> #rrggbb. Matches slotslop's rainbow helper."""
    h = h % 360.0
    c = v * s
    x = c * (1 - abs((h / 60.0) % 2 - 1))
    m = v - c
    if h < 60:
        r, g, b = c, x, 0.0
    elif h < 120:
        r, g, b = x, c, 0.0
    elif h < 180:
        r, g, b = 0.0, c, x
    elif h < 240:
        r, g, b = 0.0, x, c
    elif h < 300:
        r, g, b = x, 0.0, c
    else:
        r, g, b = c, 0.0, x

    def channel(value: float) -> str:
        return format(int(round((value + m) * 255)), "02x")

    return f"#{channel(r)}{channel(g)}{channel(b)}"


def rainbow_text(
    text: str,
    phase: float,
    *,
    speed: float = 120.0,
    spread: float = 16.0,
    bold: bool = True,
) -> Text:
    """Per-character cycling rainbow, like slotslop's logo marquee."""
    out = Text()
    style_prefix = "bold " if bold else ""
    for index, char in enumerate(text):
        hue = phase * speed + index * spread
        out.append(char, style=f"{style_prefix}{hsv_to_hex(hue)}")
    return out


def marquee_bar(width: int, phase: float, *, hue: float | None = None) -> Text:
    """Scrolling rainbow block bar (Vegas marquee)."""
    out = Text()
    for index in range(width):
        if hue is None:
            color = hsv_to_hex(-phase * 220 + index * 9)
        else:
            wave = math.sin(index * 0.35 + phase * 5) * 18
            brightness = 0.45 + 0.5 * abs(math.sin(phase * 3.5 + index * 0.25))
            color = hsv_to_hex(hue + wave, 1.0, brightness)
        out.append("█", style=color)
    return out


@dataclass
class LogoColumn:
    """One letter column in the slotslop-style logo reel."""

    target: str
    display: str = "A"
    state: ColumnState = "spin"
    wait: int = 0
    delay: int = 0

    def __post_init__(self) -> None:
        self.target = self.target.lower()
        self.display = choice(LOGO_SYMBOLS)


@dataclass
class LogoReelEngine:
    """Vegas-style logo reel: columns spin, decelerate, and lock left-to-right."""

    target: str
    columns: List[LogoColumn] = field(default_factory=list)
    frame: int = 0
    stop_at: int = 7
    spin_lead: int = 10

    def __post_init__(self) -> None:
        if not self.columns:
            letters = [ch for ch in self.target.lower() if ch.isalpha()]
            self.columns = [LogoColumn(target=ch) for ch in letters]

    @property
    def done(self) -> bool:
        return all(col.state == "stopped" for col in self.columns)

    def reset(self) -> None:
        self.frame = 0
        letters = [ch for ch in self.target.lower() if ch.isalpha()]
        self.columns = [LogoColumn(target=ch) for ch in letters]

    def _begin_stopping(self, index: int) -> None:
        if index >= len(self.columns):
            return
        col = self.columns[index]
        if col.state != "spin":
            return
        col.state = "stopping"
        col.delay = 1
        col.wait = 1

    def _step_column(self, col: LogoColumn) -> None:
        if col.state == "stopped":
            col.display = col.target.upper()
            return

        if col.state == "spin":
            col.display = choice(LOGO_SYMBOLS)
            return

        col.wait -= 1
        if col.wait > 0:
            col.display = choice(LOGO_SYMBOLS)
            return

        col.display = choice(LOGO_SYMBOLS)
        col.delay += 1
        col.wait = col.delay
        if col.delay > self.stop_at:
            col.state = "stopped"
            col.display = col.target.upper()

    def tick(self) -> None:
        """Advance one animation frame (~70ms in the UI)."""
        self.frame += 1

        if self.frame == self.spin_lead:
            self._begin_stopping(0)

        for index, col in enumerate(self.columns):
            was_stopped = col.state == "stopped"
            self._step_column(col)
            if not was_stopped and col.state == "stopped":
                self._begin_stopping(index + 1)

    def logo_width(self, *, with_slots: bool = True) -> int:
        """Cell width of the logo line (🎰 is 2 cells wide)."""
        letters = len(self.columns) * 2 - 1  # letters + single spaces
        slots = (2 + 2) * 2 if with_slots else 0  # "🎰  " on each side
        return letters + slots

    def render_logo(
        self,
        phase: float | None = None,
        *,
        with_slots: bool = True,
        marquee: bool = False,
    ) -> Text:
        """Build the spaced rainbow logo line (and optional marquee bars)."""
        if phase is None:
            phase = time.monotonic()

        logo_core = self._logo_line(phase, with_slots=with_slots)
        logo_core.no_wrap = True
        if not marquee:
            return logo_core

        width = self.logo_width(with_slots=with_slots)
        out = Text(justify="center", no_wrap=True)
        out.append_text(marquee_bar(width, phase))
        out.append("\n")
        out.append_text(logo_core)
        out.append("\n")
        out.append_text(marquee_bar(width, phase + 0.5))
        return out

    def _logo_line(self, phase: float, *, with_slots: bool = True) -> Text:
        out = Text(justify="center")
        if with_slots:
            out.append("🎰  ")

        for index, col in enumerate(self.columns):
            char = col.display.upper()
            if col.state == "stopped":
                color = hsv_to_hex(phase * 120 + index * 16)
                out.append(char, style=f"bold {color}")
            else:
                spinning_color = hsv_to_hex(phase * 180 + index * 22, 0.35, 0.85)
                out.append(char, style=f"bold {spinning_color}")
            if index < len(self.columns) - 1:
                out.append(" ")

        if with_slots:
            out.append("  🎰")
        return out


@dataclass
class ReelSpin:
    """A left-to-right slot reel reveal of a target string.

    Each character spins through random symbols, locking in sequentially
    like slot machine reels stopping one at a time.
    """

    target: str
    frames_per_lock: int = 3
    spin_lead: int = 6
    frame: int = 0

    def locked_count(self) -> int:
        return max(0, (self.frame - self.spin_lead) // self.frames_per_lock)

    @property
    def done(self) -> bool:
        return self.locked_count() >= len(self.target)

    def tick(self) -> str:
        """Advance one frame and return the current display string."""
        self.frame += 1
        locked = self.locked_count()
        out = []
        for i, ch in enumerate(self.target):
            if i < locked or not ch.isalpha():
                out.append(ch)
            else:
                out.append(choice(REEL_SYMBOLS))
        return "".join(out)


@dataclass
class Odometer:
    """Slot-style count-up: the displayed value rolls toward the target.

    Steps are proportional to the gap so big wins 'spin' fast then ease in,
    like Balatro's score tally.
    """

    value: float = 0.0
    target: float = 0.0

    def set_target(self, target: float) -> None:
        self.target = target

    def snap(self) -> None:
        self.value = self.target

    @property
    def done(self) -> bool:
        return abs(self.target - self.value) < 0.5

    def tick(self) -> int:
        """Advance toward the target; returns the current display value."""
        gap = self.target - self.value
        if abs(gap) >= 0.5:
            # Ease toward target: 25% of remaining gap, minimum 1 unit
            step = max(1.0, abs(gap) * 0.25)
            self.value += step if gap > 0 else -step

        if abs(self.target - self.value) < 0.5:
            self.value = self.target

        return int(self.value)


@dataclass
class DigitSpin:
    """Spin random digits before settling on a final number, reel by reel."""

    target: str
    frames_per_lock: int = 4
    spin_lead: int = 8
    frame: int = 0

    @classmethod
    def for_number(cls, value: int, **kwargs) -> "DigitSpin":
        return cls(target=str(value), **kwargs)

    def locked_count(self) -> int:
        return max(0, (self.frame - self.spin_lead) // self.frames_per_lock)

    @property
    def done(self) -> bool:
        return self.locked_count() >= len(self.target)

    def tick(self) -> str:
        self.frame += 1
        locked = self.locked_count()
        out: List[str] = []
        for i, ch in enumerate(self.target):
            if i < locked or not ch.isdigit():
                out.append(ch)
            else:
                out.append(str(randint(0, 9)))
        return "".join(out)
