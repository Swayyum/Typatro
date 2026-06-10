"""Slot machine animation primitives for TYPATRO.

Provides frame-based reel spin and odometer count-up logic that widgets
drive from a Textual interval timer. Pure logic — no widget dependencies —
so it stays unit-testable.
"""

from __future__ import annotations

import string
from dataclasses import dataclass, field
from random import choice, randint
from typing import List

REEL_SYMBOLS = string.ascii_lowercase
DIGIT_SYMBOLS = string.digits


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
