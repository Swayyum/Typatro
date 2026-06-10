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


def compute_target(blind: BlindDef, word_count: int) -> int:
    """Compute score target based on blind type and test length."""
    scale = word_count / 30
    return int(BASE_TARGET * blind.target_multiplier * scale)


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

    match boss:
        case BossBlind.THE_HOOK:
            config_parser.set("blind_mode", "on")
        case BossBlind.THE_WALL:
            pass  # Higher target handled in compute_target
        case BossBlind.THE_NEEDLE:
            config_parser.set("min_speed", 40)
        case BossBlind.THE_EYE:
            config_parser.set("confidence_mode", "on")
        case BossBlind.THE_PSYCHIC:
            config_parser.set("force_correct", "on")
        case _:
            pass


def clear_boss_debuffs() -> None:
    apply_boss_debuff(None)
