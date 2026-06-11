"""Blind definitions and debuff application for Balatro run mode."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from typatro.src.parser import config_parser


class BlindType(Enum):
    SMALL = "small"
    BIG = "big"
    BOSS = "boss"


class BossBlind(Enum):
    THE_HOOK = "the_hook"
    THE_WALL = "the_wall"
    THE_NEEDLE = "the_needle"
    THE_EYE = "the_eye"
    THE_PSYCHIC = "the_psychic"


@dataclass(frozen=True)
class BlindDef:
    blind_type: BlindType
    name: str
    target_multiplier: float
    reward: str
    boss: Optional[BossBlind] = None

    @property
    def display_name(self) -> str:
        if self.boss:
            return f"{self.name} ({self.boss.value.replace('_', ' ').title()})"
        return self.name


# Base targets scale with word count / duration
BASE_TARGET = 300

# Exponential per-ante growth, expressed as an exact ratio (8/5 = 1.6x per
# ante) so targets stay precise integers at arbitrarily high antes — Balatro
# requirements grow roughly exponentially and can reach 1e308+.
ANTE_GROWTH_NUM = 8
ANTE_GROWTH_DEN = 5


def ante_scale_target(target: int, ante: int) -> int:
    """Scale a base target exponentially by ante using exact integer math."""
    steps = max(0, ante - 1)
    return target * ANTE_GROWTH_NUM**steps // ANTE_GROWTH_DEN**steps


def compute_target(blind: BlindDef, word_count: int, ante: int = 1) -> int:
    """Compute score target based on blind type, test length, and ante."""
    # Keep the multiplier in integer space (multipliers are defined to 1dp)
    base = BASE_TARGET * int(blind.target_multiplier * 10) * word_count // (30 * 10)
    return ante_scale_target(base, ante)


SMALL_BLIND = BlindDef(BlindType.SMALL, "Small Blind", 1.0, "+1 Joker pick")
BIG_BLIND = BlindDef(BlindType.BIG, "Big Blind", 1.5, "+1 Joker pick")
BOSS_BLINDS = [
    BlindDef(BlindType.BOSS, "The Hook", 2.0, "+1 Joker pick", BossBlind.THE_HOOK),
    BlindDef(BlindType.BOSS, "The Wall", 2.5, "+1 Joker pick", BossBlind.THE_WALL),
    BlindDef(BlindType.BOSS, "The Needle", 2.0, "+1 Joker pick", BossBlind.THE_NEEDLE),
    BlindDef(BlindType.BOSS, "The Eye", 2.0, "+1 Joker pick", BossBlind.THE_EYE),
    BlindDef(BlindType.BOSS, "The Psychic", 2.2, "+1 Joker pick", BossBlind.THE_PSYCHIC),
]

ANTE_BLINDS: List[BlindDef] = [SMALL_BLIND, BIG_BLIND] + BOSS_BLINDS[:1]


def get_blind_for_index(index: int, ante: int) -> BlindDef:
    """Return the blind for a given index within an ante."""
    if index == 0:
        return SMALL_BLIND
    if index == 1:
        return BIG_BLIND
    boss_idx = (ante - 1) % len(BOSS_BLINDS)
    return BOSS_BLINDS[boss_idx]


def apply_boss_debuff(boss: Optional[BossBlind]) -> None:
    """Apply boss blind debuff via typatro config tweaks."""
    # Reset debuffs first
    config_parser.set("blind_mode", False)
    config_parser.set("min_speed", 0)
    config_parser.set("confidence_mode", "off")
    config_parser.set("force_correct", False)

    if not boss:
        return

    if boss == BossBlind.THE_HOOK:
        config_parser.set("blind_mode", "on")
    elif boss == BossBlind.THE_WALL:
        pass  # Higher target handled in compute_target
    elif boss == BossBlind.THE_NEEDLE:
        config_parser.set("min_speed", 40)
    elif boss == BossBlind.THE_EYE:
        config_parser.set("confidence_mode", "on")
    elif boss == BossBlind.THE_PSYCHIC:
        config_parser.set("force_correct", "on")


def clear_boss_debuffs() -> None:
    apply_boss_debuff(None)
